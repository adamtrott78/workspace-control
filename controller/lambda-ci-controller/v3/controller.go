package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log/slog"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/actions/scaleset"
	"github.com/actions/scaleset/listener"
)

const (
	defaultV3ProvisionerSocket = "/run/workspace-ci/v3/provisioner.sock"
	defaultV3StateRoot         = "/var/lib/workspace-ci/v3/controller/state"
)

type trustedWorkflow struct {
	RouteID                      string   `json:"route_id"`
	Path                         string   `json:"path"`
	DefaultBranch                string   `json:"default_branch"`
	BlobSHA                      string   `json:"blob_sha"`
	CompileTimeJobKey            string   `json:"compile_time_job_key"`
	CompileTimeTopLevelJobCount  int      `json:"compile_time_top_level_job_count"`
	AllowedEvents                []string `json:"allowed_events"`
	AllowedActorLogins           []string `json:"allowed_actor_logins"`
}

type controllerPolicy struct {
	SchemaVersion                  int               `json:"schema_version"`
	RunnerClassID                  string            `json:"runner_class_id"`
	Repository                     string            `json:"repository"`
	ScaleSetName                   string            `json:"scale_set_name"`
	RunnerPrefix                   string            `json:"runner_prefix"`
	MaxRunners                     int               `json:"max_runners"`
	TrustedWorkflows               []trustedWorkflow `json:"trusted_workflows"`
	ControlPlaneGenerationSHA256   string            `json:"control_plane_generation_sha256"`
	ControllerPolicySHA256         string            `json:"controller_policy_sha256"`
}

func loadControllerPolicy(path string) (controllerPolicy, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return controllerPolicy{}, fmt.Errorf("read controller policy: %w", err)
	}
	var policy controllerPolicy
	if err := json.Unmarshal(raw, &policy); err != nil {
		return controllerPolicy{}, fmt.Errorf("decode controller policy: %w", err)
	}
	if policy.SchemaVersion != 1 {
		return controllerPolicy{}, fmt.Errorf("controller policy schema_version must be 1")
	}
	if strings.TrimSpace(policy.RunnerClassID) == "" ||
		strings.TrimSpace(policy.Repository) == "" ||
		strings.TrimSpace(policy.ScaleSetName) == "" ||
		strings.TrimSpace(policy.RunnerPrefix) == "" {
		return controllerPolicy{}, fmt.Errorf("controller policy identity is incomplete")
	}
	if policy.MaxRunners <= 0 {
		return controllerPolicy{}, fmt.Errorf("controller policy max_runners must be positive")
	}
	if !strings.HasPrefix(policy.RunnerPrefix, "lambda-") ||
		!strings.HasSuffix(policy.RunnerPrefix, "-") {
		return controllerPolicy{}, fmt.Errorf("controller runner_prefix is invalid")
	}
	if len(policy.ControlPlaneGenerationSHA256) != 64 ||
		len(policy.ControllerPolicySHA256) != 64 {
		return controllerPolicy{}, fmt.Errorf("controller policy digest is invalid")
	}
	if len(policy.TrustedWorkflows) == 0 {
		return controllerPolicy{}, fmt.Errorf("controller policy trusted_workflows is empty")
	}
	seen := map[string]struct{}{}
	for _, workflow := range policy.TrustedWorkflows {
		if workflow.Path == "" || !strings.HasPrefix(workflow.Path, ".github/workflows/") {
			return controllerPolicy{}, fmt.Errorf("trusted workflow path is invalid: %q", workflow.Path)
		}
		if workflow.DefaultBranch == "" || len(workflow.BlobSHA) != 40 {
			return controllerPolicy{}, fmt.Errorf("trusted workflow identity is incomplete: %s", workflow.Path)
		}
		if workflow.CompileTimeTopLevelJobCount != 1 {
			return controllerPolicy{}, fmt.Errorf("trusted workflow must have one compiled top-level job: %s", workflow.Path)
		}
		if len(workflow.AllowedEvents) == 0 || len(workflow.AllowedActorLogins) == 0 {
			return controllerPolicy{}, fmt.Errorf("trusted workflow allowlists are empty: %s", workflow.Path)
		}
		if _, exists := seen[workflow.Path]; exists {
			return controllerPolicy{}, fmt.Errorf("duplicate trusted workflow path: %s", workflow.Path)
		}
		seen[workflow.Path] = struct{}{}
	}
	return policy, nil
}

type verifiedJob struct {
	RunnerRequestID        int64
	WorkflowRunID          int64
	WorkflowPath           string
	WorkflowBlobSHA        string
	ActorLogin             string
	TriggeringActorLogin   string
	EventName              string
}

type jobVerifier interface {
	Verify(context.Context, *scaleset.JobMessageBase) (verifiedJob, bool, string, error)
}

type capacityResponse struct {
	SchemaVersion          int    `json:"schema_version"`
	Operation              string `json:"operation"`
	Status                 string `json:"status"`
	RequestID              string `json:"request_id"`
	ReceiptStatus          string `json:"receipt_status,omitempty"`
	RunnerName             string `json:"runner_name,omitempty"`
	ReservationExpiresAt   string `json:"reservation_expires_at,omitempty"`
	ErrorCode              string `json:"error_code,omitempty"`
	Error                  string `json:"error,omitempty"`
}

type capacityClient interface {
	Reserve(context.Context, string, string) (capacityResponse, error)
	Launch(context.Context, string, string, string) (capacityResponse, error)
	Status(context.Context, string) (capacityResponse, error)
	Cancel(context.Context, string) (capacityResponse, error)
}

type runnerJITClient interface {
	GenerateJitRunnerConfig(
		context.Context,
		*scaleset.RunnerScaleSetJitRunnerSetting,
		int,
	) (*scaleset.RunnerScaleSetJitRunnerConfig, error)
	RemoveRunner(context.Context, int64) error
}

type jobAcquirer interface {
	AcquireJobs(context.Context, []int64) ([]int64, error)
}

type jobRecord struct {
	SchemaVersion             int    `json:"schema_version"`
	ControllerPolicySHA256    string `json:"controller_policy_sha256"`
	RunnerRequestID           int64  `json:"runner_request_id"`
	WorkflowRunID             int64  `json:"workflow_run_id"`
	WorkflowPath              string `json:"workflow_path"`
	WorkflowBlobSHA           string `json:"workflow_blob_sha"`
	RequestID                 string `json:"request_id"`
	RunnerName                string `json:"runner_name"`
	ProvisionAttempt          int    `json:"provision_attempt"`
	State                     string `json:"state"`
	SchedulerState            string `json:"scheduler_state"`
	LastRootStatus            string `json:"last_root_status,omitempty"`
	JITRunnerID               int64  `json:"jit_runner_id,omitempty"`
	JITSHA256                 string `json:"jit_sha256,omitempty"`
	RetryCount                int    `json:"retry_count,omitempty"`
	NextRetryAt               string `json:"next_retry_at,omitempty"`
	UpdatedAt                 string `json:"updated_at"`
}

func (r jobRecord) terminal() bool {
	switch r.State {
	case "COMPLETED", "FAILED", "CANCELED":
		return true
	default:
		return false
	}
}

func (r jobRecord) rootCapacityHeld() bool {
	switch r.State {
	case "RESERVED", "JIT_REGISTERED", "PREPARING", "ACCEPTED", "RUNNING":
		return true
	default:
		return false
	}
}

type ledgerStore interface {
	List() ([]jobRecord, error)
	Get(int64) (jobRecord, bool, error)
	Put(jobRecord) error
}

type fileLedger struct {
	root string
	mu   sync.Mutex
}

func newFileLedger(root string) (*fileLedger, error) {
	if !filepath.IsAbs(root) {
		return nil, fmt.Errorf("controller state root must be absolute")
	}
	if err := os.MkdirAll(root, 0o700); err != nil {
		return nil, fmt.Errorf("create controller state root: %w", err)
	}
	if err := os.Chmod(root, 0o700); err != nil {
		return nil, fmt.Errorf("chmod controller state root: %w", err)
	}
	return &fileLedger{root: root}, nil
}

func (l *fileLedger) path(runnerRequestID int64) string {
	return filepath.Join(l.root, fmt.Sprintf("scheduler-%d.json", runnerRequestID))
}

func (l *fileLedger) List() ([]jobRecord, error) {
	l.mu.Lock()
	defer l.mu.Unlock()
	entries, err := os.ReadDir(l.root)
	if err != nil {
		return nil, err
	}
	records := make([]jobRecord, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasPrefix(entry.Name(), "scheduler-") || !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}
		raw, err := os.ReadFile(filepath.Join(l.root, entry.Name()))
		if err != nil {
			return nil, err
		}
		var record jobRecord
		if err := json.Unmarshal(raw, &record); err != nil {
			return nil, fmt.Errorf("decode ledger %s: %w", entry.Name(), err)
		}
		if record.SchemaVersion != 1 || record.RunnerRequestID <= 0 {
			return nil, fmt.Errorf("ledger %s is invalid", entry.Name())
		}
		records = append(records, record)
	}
	sort.Slice(records, func(i, j int) bool {
		return records[i].RunnerRequestID < records[j].RunnerRequestID
	})
	return records, nil
}

func (l *fileLedger) Get(runnerRequestID int64) (jobRecord, bool, error) {
	l.mu.Lock()
	defer l.mu.Unlock()
	raw, err := os.ReadFile(l.path(runnerRequestID))
	if os.IsNotExist(err) {
		return jobRecord{}, false, nil
	}
	if err != nil {
		return jobRecord{}, false, err
	}
	var record jobRecord
	if err := json.Unmarshal(raw, &record); err != nil {
		return jobRecord{}, false, err
	}
	if record.SchemaVersion != 1 || record.RunnerRequestID != runnerRequestID {
		return jobRecord{}, false, fmt.Errorf("durable scheduler ledger identity mismatch")
	}
	return record, true, nil
}

func (l *fileLedger) Put(record jobRecord) error {
	if record.RunnerRequestID <= 0 {
		return fmt.Errorf("runner_request_id must be positive")
	}
	record.SchemaVersion = 1
	raw, err := json.MarshalIndent(record, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')

	l.mu.Lock()
	defer l.mu.Unlock()
	path := l.path(record.RunnerRequestID)
	tmp := path + fmt.Sprintf(".%d.tmp", os.Getpid())
	if err := os.WriteFile(tmp, raw, 0o600); err != nil {
		return err
	}
	if err := os.Chmod(tmp, 0o600); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	if err := os.Rename(tmp, path); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	return nil
}

func deriveProvisionIdentity(policy controllerPolicy, job verifiedJob, attempt int) (string, string, error) {
	if attempt < 0 {
		return "", "", fmt.Errorf("provision attempt cannot be negative")
	}
	material := fmt.Sprintf(
		"%s|%d|%d|%s|%s|%d",
		policy.RunnerClassID,
		job.RunnerRequestID,
		job.WorkflowRunID,
		job.WorkflowPath,
		job.WorkflowBlobSHA,
		attempt,
	)
	sum := sha256.Sum256([]byte(material))
	raw := append([]byte(nil), sum[:16]...)
	raw[6] = (raw[6] & 0x0f) | 0x50
	raw[8] = (raw[8] & 0x3f) | 0x80
	h := hex.EncodeToString(raw)
	requestID := fmt.Sprintf(
		"%s-%s-%s-%s-%s",
		h[0:8], h[8:12], h[12:16], h[16:20], h[20:32],
	)
	runnerName := policy.RunnerPrefix + hex.EncodeToString(sum[16:22])
	if len(runnerName) > 128 {
		return "", "", fmt.Errorf("derived runner name exceeds protocol bound")
	}
	return requestID, runnerName, nil
}

func newJobRecord(policy controllerPolicy, job verifiedJob, state string, now time.Time) (jobRecord, error) {
	requestID, runnerName, err := deriveProvisionIdentity(policy, job, 0)
	if err != nil {
		return jobRecord{}, err
	}
	return jobRecord{
		SchemaVersion:          1,
		ControllerPolicySHA256: policy.ControllerPolicySHA256,
		RunnerRequestID:        job.RunnerRequestID,
		WorkflowRunID:          job.WorkflowRunID,
		WorkflowPath:           job.WorkflowPath,
		WorkflowBlobSHA:        job.WorkflowBlobSHA,
		RequestID:              requestID,
		RunnerName:             runnerName,
		ProvisionAttempt:       0,
		State:                  state,
		SchedulerState:         state,
		UpdatedAt:              now.UTC().Format(time.RFC3339Nano),
	}, nil
}

func verifiedFromRecord(record jobRecord) verifiedJob {
	return verifiedJob{
		RunnerRequestID: record.RunnerRequestID,
		WorkflowRunID:   record.WorkflowRunID,
		WorkflowPath:    record.WorkflowPath,
		WorkflowBlobSHA: record.WorkflowBlobSHA,
	}
}

func resetFreshAttempt(policy controllerPolicy, record *jobRecord, now time.Time) error {
	record.ProvisionAttempt++
	requestID, runnerName, err := deriveProvisionIdentity(
		policy,
		verifiedFromRecord(*record),
		record.ProvisionAttempt,
	)
	if err != nil {
		return err
	}
	record.RequestID = requestID
	record.RunnerName = runnerName
	record.State = "ACQUIRED"
	record.LastRootStatus = ""
	record.JITRunnerID = 0
	record.JITSHA256 = ""
	record.RetryCount = 0
	record.NextRetryAt = ""
	record.UpdatedAt = now.UTC().Format(time.RFC3339Nano)
	return nil
}

type v3Scaler struct {
	policy       controllerPolicy
	verifier     jobVerifier
	ledger       ledgerStore
	session      jobAcquirer
	jit          runnerJITClient
	root         capacityClient
	scaleSetID   int
	logger       *slog.Logger
	now          func() time.Time
	lastStats    *scaleset.RunnerScaleSetStatistic
	mu           sync.Mutex
}

func (s *v3Scaler) desiredCapacity(stats *scaleset.RunnerScaleSetStatistic) int {
	if stats == nil {
		return 0
	}
	target := stats.TotalAssignedJobs
	if target < 0 {
		target = 0
	}
	if target > s.policy.MaxRunners {
		target = s.policy.MaxRunners
	}
	return target
}

func containsString(values []string, wanted string) bool {
	for _, value := range values {
		if value == wanted {
			return true
		}
	}
	return false
}

func (s *v3Scaler) verifyPolicyRecord(record jobRecord) error {
	if record.ControllerPolicySHA256 != s.policy.ControllerPolicySHA256 {
		return fmt.Errorf(
			"durable controller-policy binding mismatch for runner_request_id=%d",
			record.RunnerRequestID,
		)
	}
	return nil
}

func (s *v3Scaler) outstandingAcquired(records []jobRecord) int {
	total := 0
	for _, record := range records {
		if record.terminal() {
			continue
		}
		switch record.State {
		case "ADMITTED", "ACQUIRED", "WAITING_CAPACITY", "RESERVED", "JIT_REGISTERED", "PREPARING", "ACCEPTED", "RUNNING":
			total++
		}
	}
	return total
}

func (s *v3Scaler) processAvailable(
	ctx context.Context,
	jobs []*scaleset.JobAvailable,
) error {
	records, err := s.ledger.List()
	if err != nil {
		return fmt.Errorf("list controller ledger: %w", err)
	}
	capacity := s.policy.MaxRunners - s.outstandingAcquired(records)
	if capacity <= 0 {
		return nil
	}

	requestIDs := make([]int64, 0, capacity)
	staged := make(map[int64]jobRecord)
	for _, job := range jobs {
		if capacity <= 0 {
			break
		}
		if job == nil || job.RunnerRequestID <= 0 {
			continue
		}
		existing, ok, err := s.ledger.Get(job.RunnerRequestID)
		if err != nil {
			return fmt.Errorf("read controller ledger: %w", err)
		}
		if ok {
			if err := s.verifyPolicyRecord(existing); err != nil {
				return err
			}
			if existing.State != "ADMITTED" {
				continue
			}
			requestIDs = append(requestIDs, job.RunnerRequestID)
			staged[job.RunnerRequestID] = existing
			capacity--
			continue
		}

		verified, trusted, reason, err := s.verifier.Verify(ctx, &job.JobMessageBase)
		if err != nil {
			return fmt.Errorf("verify JobAvailable structured identity: %w", err)
		}
		if !trusted {
			s.logger.Warn(
				"Ignoring anomalous untrusted JobAvailable",
				slog.Int64("runner_request_id", job.RunnerRequestID),
				slog.Int64("workflow_run_id", job.WorkflowRunID),
				slog.String("reason", reason),
			)
			continue
		}
		record, err := newJobRecord(s.policy, verified, "ADMITTED", s.now())
		if err != nil {
			return err
		}
		if err := s.ledger.Put(record); err != nil {
			return fmt.Errorf("persist admitted scheduler job: %w", err)
		}
		requestIDs = append(requestIDs, job.RunnerRequestID)
		staged[job.RunnerRequestID] = record
		capacity--
	}
	if len(requestIDs) == 0 {
		return nil
	}

	acquired, err := s.session.AcquireJobs(ctx, requestIDs)
	if err != nil {
		return fmt.Errorf("acquire trusted scheduler jobs: %w", err)
	}
	acquiredSet := make(map[int64]struct{}, len(acquired))
	for _, id := range acquired {
		acquiredSet[id] = struct{}{}
	}
	for _, id := range requestIDs {
		if _, ok := acquiredSet[id]; !ok {
			continue
		}
		record := staged[id]
		record.State = "ACQUIRED"
		record.SchedulerState = "ACQUIRED"
		record.UpdatedAt = s.now().UTC().Format(time.RFC3339Nano)
		if err := s.ledger.Put(record); err != nil {
			return fmt.Errorf("persist acquired scheduler job: %w", err)
		}
	}
	return nil
}

func (s *v3Scaler) processAssigned(
	ctx context.Context,
	jobs []*scaleset.JobAssigned,
) error {
	for _, job := range jobs {
		if job == nil || job.RunnerRequestID <= 0 {
			s.logger.Warn("Ignoring JobAssigned without positive runner_request_id")
			continue
		}
		record, ok, err := s.ledger.Get(job.RunnerRequestID)
		if err != nil {
			return err
		}
		if ok {
			if err := s.verifyPolicyRecord(record); err != nil {
				return err
			}
			if !record.terminal() && record.State == "ADMITTED" {
				record.State = "ACQUIRED"
			}
			record.SchedulerState = "ASSIGNED"
			record.UpdatedAt = s.now().UTC().Format(time.RFC3339Nano)
			if err := s.ledger.Put(record); err != nil {
				return err
			}
			continue
		}

		verified, trusted, reason, err := s.verifier.Verify(ctx, &job.JobMessageBase)
		if err != nil {
			return fmt.Errorf("verify JobAssigned structured identity: %w", err)
		}
		if !trusted {
			s.logger.Warn(
				"Ignoring anomalous untrusted JobAssigned",
				slog.Int64("runner_request_id", job.RunnerRequestID),
				slog.Int64("workflow_run_id", job.WorkflowRunID),
				slog.String("reason", reason),
			)
			continue
		}
		record, err = newJobRecord(s.policy, verified, "ACQUIRED", s.now())
		if err != nil {
			return err
		}
		record.SchedulerState = "ASSIGNED"
		if err := s.ledger.Put(record); err != nil {
			return err
		}
	}
	return nil
}

func (s *v3Scaler) processLifecycle(
	started []*scaleset.JobStarted,
	completed []*scaleset.JobCompleted,
) error {
	records, err := s.ledger.List()
	if err != nil {
		return err
	}
	byRunner := make(map[string]jobRecord, len(records))
	for _, record := range records {
		if err := s.verifyPolicyRecord(record); err != nil {
			return err
		}
		byRunner[record.RunnerName] = record
	}
	for _, job := range started {
		if job == nil {
			continue
		}
		record, ok := byRunner[job.RunnerName]
		if !ok {
			continue
		}
		record.SchedulerState = "STARTED"
		if record.State == "ACCEPTED" || record.State == "PREPARING" {
			record.State = "RUNNING"
		}
		record.UpdatedAt = s.now().UTC().Format(time.RFC3339Nano)
		if err := s.ledger.Put(record); err != nil {
			return err
		}
		byRunner[record.RunnerName] = record
	}
	for _, job := range completed {
		if job == nil {
			continue
		}
		record, ok := byRunner[job.RunnerName]
		if !ok {
			continue
		}
		record.SchedulerState = "COMPLETED"
		record.UpdatedAt = s.now().UTC().Format(time.RFC3339Nano)
		if err := s.ledger.Put(record); err != nil {
			return err
		}
	}
	return nil
}

func (s *v3Scaler) removeOrphanJIT(ctx context.Context, record *jobRecord) error {
	if record.JITRunnerID <= 0 {
		record.JITSHA256 = ""
		return nil
	}
	if err := s.jit.RemoveRunner(ctx, record.JITRunnerID); err != nil {
		return fmt.Errorf("remove orphan JIT runner id=%d: %w", record.JITRunnerID, err)
	}
	record.JITRunnerID = 0
	record.JITSHA256 = ""
	return nil
}

func (s *v3Scaler) recoverOne(ctx context.Context, record *jobRecord) error {
	switch record.State {
	case "ADMITTED", "ACQUIRED", "WAITING_CAPACITY":
		return nil
	}
	if record.terminal() {
		return nil
	}

	status, err := s.root.Status(ctx, record.RequestID)
	if err != nil {
		return fmt.Errorf("query root status: %w", err)
	}
	record.LastRootStatus = status.Status
	now := s.now()

	switch status.Status {
	case "MISSING":
		if err := s.removeOrphanJIT(ctx, record); err != nil {
			return err
		}
		record.State = "ACQUIRED"
	case "RESERVED":
		if record.State == "JIT_REGISTERED" {
			if err := s.removeOrphanJIT(ctx, record); err != nil {
				return err
			}
		}
		record.State = "RESERVED"
	case "PREPARING":
		record.State = "PREPARING"
	case "ACCEPTED":
		record.State = "ACCEPTED"
		record.JITRunnerID = 0
		record.JITSHA256 = ""
	case "COMPLETED", "FAILED":
		if record.JITRunnerID > 0 && record.State != "ACCEPTED" && record.State != "RUNNING" {
			if err := s.removeOrphanJIT(ctx, record); err != nil {
				return err
			}
		}
		record.State = status.Status
	case "CANCELED":
		if err := s.removeOrphanJIT(ctx, record); err != nil {
			return err
		}
		if record.SchedulerState == "COMPLETED" {
			record.State = "CANCELED"
		} else if err := resetFreshAttempt(s.policy, record, now); err != nil {
			return err
		}
	default:
		return fmt.Errorf("root returned unsupported STATUS result %q", status.Status)
	}
	record.UpdatedAt = now.UTC().Format(time.RFC3339Nano)
	return s.ledger.Put(*record)
}

func (s *v3Scaler) scheduleCapacityRetry(record *jobRecord) error {
	record.State = "WAITING_CAPACITY"
	record.RetryCount++
	delay := time.Second << minInt(record.RetryCount-1, 6)
	if delay > time.Minute {
		delay = time.Minute
	}
	record.NextRetryAt = s.now().Add(delay).UTC().Format(time.RFC3339Nano)
	record.UpdatedAt = s.now().UTC().Format(time.RFC3339Nano)
	return s.ledger.Put(*record)
}

func retryDue(record jobRecord, now time.Time) bool {
	if record.NextRetryAt == "" {
		return true
	}
	at, err := time.Parse(time.RFC3339Nano, record.NextRetryAt)
	if err != nil {
		return true
	}
	return !now.Before(at)
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func (s *v3Scaler) reserve(ctx context.Context, record *jobRecord) (bool, error) {
	response, err := s.root.Reserve(ctx, record.RequestID, record.RunnerName)
	if err != nil {
		return false, fmt.Errorf("root RESERVE: %w", err)
	}
	record.LastRootStatus = response.Status
	record.UpdatedAt = s.now().UTC().Format(time.RFC3339Nano)

	switch response.Status {
	case "RESERVED":
		record.State = "RESERVED"
		record.RetryCount = 0
		record.NextRetryAt = ""
	case "DUPLICATE":
		switch response.ReceiptStatus {
		case "RESERVED":
			record.State = "RESERVED"
		case "ACCEPTED":
			record.State = "ACCEPTED"
		case "COMPLETED", "FAILED":
			record.State = response.ReceiptStatus
		case "CANCELED":
			if err := resetFreshAttempt(s.policy, record, s.now()); err != nil {
				return false, err
			}
			return false, s.ledger.Put(*record)
		default:
			return false, fmt.Errorf("root duplicate RESERVE receipt invalid: %q", response.ReceiptStatus)
		}
	case "BUSY", "CLASS_QUARANTINED":
		if err := s.scheduleCapacityRetry(record); err != nil {
			return false, err
		}
		return false, nil
	case "INVALID_REQUEST", "UNAUTHORIZED_PEER":
		return false, fmt.Errorf(
			"fatal root RESERVE protocol rejection status=%s code=%s error=%s",
			response.Status, response.ErrorCode, response.Error,
		)
	default:
		return false, fmt.Errorf("root RESERVE status invalid: %q", response.Status)
	}
	if err := s.ledger.Put(*record); err != nil {
		return false, err
	}
	return record.State == "RESERVED", nil
}

func (s *v3Scaler) generateAndLaunch(ctx context.Context, record *jobRecord) error {
	jit, err := s.jit.GenerateJitRunnerConfig(
		ctx,
		&scaleset.RunnerScaleSetJitRunnerSetting{Name: record.RunnerName},
		s.scaleSetID,
	)
	if err != nil {
		return fmt.Errorf("generate JIT after root reservation: %w", err)
	}
	if jit == nil || jit.Runner == nil || jit.Runner.ID <= 0 || jit.EncodedJITConfig == "" {
		return fmt.Errorf("JIT response is incomplete")
	}
	raw := jit.EncodedJITConfig
	sum := sha256.Sum256([]byte(raw))
	record.JITRunnerID = int64(jit.Runner.ID)
	record.JITSHA256 = hex.EncodeToString(sum[:])
	record.State = "JIT_REGISTERED"
	record.UpdatedAt = s.now().UTC().Format(time.RFC3339Nano)
	if err := s.ledger.Put(*record); err != nil {
		_ = s.jit.RemoveRunner(context.WithoutCancel(ctx), record.JITRunnerID)
		return err
	}

	response, err := s.root.Launch(ctx, record.RequestID, record.RunnerName, raw)
	raw = ""
	if err != nil {
		return fmt.Errorf("root LAUNCH: %w", err)
	}
	record.LastRootStatus = response.Status
	record.UpdatedAt = s.now().UTC().Format(time.RFC3339Nano)

	switch response.Status {
	case "PREPARING":
		record.State = "PREPARING"
	case "ACCEPTED":
		record.State = "ACCEPTED"
	case "DUPLICATE":
		switch response.ReceiptStatus {
		case "ACCEPTED":
			record.State = "ACCEPTED"
		case "COMPLETED", "FAILED":
			record.State = response.ReceiptStatus
		default:
			return fmt.Errorf("root duplicate LAUNCH receipt invalid: %q", response.ReceiptStatus)
		}
	case "FAILED":
		if err := s.removeOrphanJIT(ctx, record); err != nil {
			return err
		}
		record.State = "FAILED"
	case "RESERVATION_EXPIRED":
		if err := s.removeOrphanJIT(ctx, record); err != nil {
			return err
		}
		if err := resetFreshAttempt(s.policy, record, s.now()); err != nil {
			return err
		}
	case "INVALID_REQUEST", "UNAUTHORIZED_PEER":
		return fmt.Errorf(
			"fatal root LAUNCH protocol rejection status=%s code=%s error=%s",
			response.Status, response.ErrorCode, response.Error,
		)
	default:
		return fmt.Errorf("root LAUNCH status invalid: %q", response.Status)
	}
	if record.State == "PREPARING" || record.State == "ACCEPTED" {
		// Root owns the JIT handoff after LAUNCH. Never remove it from GitHub
		// based only on controller-side response loss.
		record.JITRunnerID = 0
		record.JITSHA256 = ""
	}
	return s.ledger.Put(*record)
}

func (s *v3Scaler) progressReserved(ctx context.Context, records []jobRecord) error {
	for i := range records {
		record := records[i]
		if err := s.verifyPolicyRecord(record); err != nil {
			return err
		}
		if err := s.recoverOne(ctx, &record); err != nil {
			return err
		}
		current, ok, err := s.ledger.Get(record.RunnerRequestID)
		if err != nil || !ok {
			if err != nil {
				return err
			}
			continue
		}
		if current.State == "RESERVED" {
			if err := s.generateAndLaunch(ctx, &current); err != nil {
				return err
			}
		}
	}
	return nil
}

func (s *v3Scaler) reconcileCapacity(ctx context.Context, stats *scaleset.RunnerScaleSetStatistic) error {
	records, err := s.ledger.List()
	if err != nil {
		return err
	}
	if err := s.progressReserved(ctx, records); err != nil {
		return err
	}

	records, err = s.ledger.List()
	if err != nil {
		return err
	}
	desired := s.desiredCapacity(stats)
	held := 0
	for _, record := range records {
		if record.rootCapacityHeld() {
			held++
		}
	}

	if held > desired {
		for i := range records {
			if held <= desired {
				break
			}
			record := records[i]
			if record.State != "RESERVED" && record.State != "JIT_REGISTERED" {
				continue
			}
			response, err := s.root.Cancel(ctx, record.RequestID)
			if err != nil {
				return fmt.Errorf("cancel excess root reservation: %w", err)
			}
			switch response.Status {
			case "CANCELED", "ALREADY_TERMINAL":
				if err := s.removeOrphanJIT(ctx, &record); err != nil {
					return err
				}
				record.State = "CANCELED"
				record.UpdatedAt = s.now().UTC().Format(time.RFC3339Nano)
				if err := s.ledger.Put(record); err != nil {
					return err
				}
				held--
			case "NOT_CANCELABLE":
				// Root crossed the accepted boundary; leave it counted.
			case "MISSING":
				if err := s.removeOrphanJIT(ctx, &record); err != nil {
					return err
				}
				record.State = "CANCELED"
				if err := s.ledger.Put(record); err != nil {
					return err
				}
				held--
			default:
				return fmt.Errorf("root CANCEL status invalid: %q", response.Status)
			}
		}
	}

	if held >= desired {
		return nil
	}

	records, err = s.ledger.List()
	if err != nil {
		return err
	}
	for i := range records {
		if held >= desired {
			break
		}
		record := records[i]
		if record.SchedulerState == "COMPLETED" {
			continue
		}
		if record.State != "ACQUIRED" && record.State != "WAITING_CAPACITY" {
			continue
		}
		if record.State == "WAITING_CAPACITY" && !retryDue(record, s.now()) {
			continue
		}
		reserved, err := s.reserve(ctx, &record)
		if err != nil {
			return err
		}
		if !reserved {
			continue
		}
		held++
		if err := s.generateAndLaunch(ctx, &record); err != nil {
			return err
		}
	}
	return nil
}

func (s *v3Scaler) Scale(ctx context.Context, msg *scaleset.RunnerScaleSetMessage) error {
	s.mu.Lock()
	if msg != nil && msg.Statistics != nil {
		copyStats := *msg.Statistics
		s.lastStats = &copyStats
	}
	stats := s.lastStats
	s.mu.Unlock()

	if msg != nil {
		if err := s.processLifecycle(msg.JobStartedMessages, msg.JobCompletedMessages); err != nil {
			return fmt.Errorf("process scheduler lifecycle: %w", err)
		}
		if err := s.processAssigned(ctx, msg.JobAssignedMessages); err != nil {
			return fmt.Errorf("process JobAssigned: %w", err)
		}
		if err := s.processAvailable(ctx, msg.JobAvailableMessages); err != nil {
			return fmt.Errorf("process JobAvailable: %w", err)
		}
	}
	return s.reconcileCapacity(ctx, stats)
}

type retryingSessionClient struct {
	inner      listener.Client
	logger     *slog.Logger
	maxBackoff time.Duration
}

func sleepContext(ctx context.Context, delay time.Duration) error {
	timer := time.NewTimer(delay)
	defer timer.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-timer.C:
		return nil
	}
}

func retryDelay(attempt int, max time.Duration) time.Duration {
	if attempt < 0 {
		attempt = 0
	}
	delay := time.Second << minInt(attempt, 6)
	if delay > max {
		return max
	}
	return delay
}

func (c *retryingSessionClient) GetMessage(
	ctx context.Context,
	lastMessageID, maxCapacity int,
) (*scaleset.RunnerScaleSetMessage, error) {
	for attempt := 0; ; attempt++ {
		value, err := c.inner.GetMessage(ctx, lastMessageID, maxCapacity)
		if err == nil {
			return value, nil
		}
		delay := retryDelay(attempt, c.maxBackoff)
		c.logger.Warn("Retrying scale-set GetMessage in process", slog.String("error", err.Error()), slog.Duration("backoff", delay))
		if err := sleepContext(ctx, delay); err != nil {
			return nil, err
		}
	}
}

func (c *retryingSessionClient) DeleteMessage(ctx context.Context, messageID int) error {
	for attempt := 0; ; attempt++ {
		err := c.inner.DeleteMessage(ctx, messageID)
		if err == nil {
			return nil
		}
		delay := retryDelay(attempt, c.maxBackoff)
		c.logger.Warn("Retrying scale-set DeleteMessage in process", slog.String("error", err.Error()), slog.Duration("backoff", delay))
		if err := sleepContext(ctx, delay); err != nil {
			return err
		}
	}
}

func (c *retryingSessionClient) AcquireJobs(ctx context.Context, ids []int64) ([]int64, error) {
	for attempt := 0; ; attempt++ {
		value, err := c.inner.AcquireJobs(ctx, ids)
		if err == nil {
			return value, nil
		}
		delay := retryDelay(attempt, c.maxBackoff)
		c.logger.Warn("Retrying scale-set AcquireJobs in process", slog.String("error", err.Error()), slog.Duration("backoff", delay))
		if err := sleepContext(ctx, delay); err != nil {
			return nil, err
		}
	}
}

func (c *retryingSessionClient) Session() scaleset.RunnerScaleSetSession {
	return c.inner.Session()
}

func parsePositiveInt64(value string, field string) (int64, error) {
	parsed, err := strconv.ParseInt(strings.TrimSpace(value), 10, 64)
	if err != nil || parsed <= 0 {
		return 0, fmt.Errorf("%s must be positive integer", field)
	}
	return parsed, nil
}
