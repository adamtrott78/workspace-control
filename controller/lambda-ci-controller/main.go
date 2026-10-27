package main

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/actions/scaleset"
	"github.com/actions/scaleset/listener"
)

const (
	defaultProvisionerSock     = "/run/workspace-ci/provisioner.sock"
	defaultControllerStateRoot = "/var/lib/workspace-ci/controller/state"
	maxRunners                 = 1
)

var (
	projectIDPattern = regexp.MustCompile(`^[a-z][a-z0-9-]{1,20}$`)
	routeIDPattern   = regexp.MustCompile(`^[a-z][a-z0-9-]{0,63}$`)
)

type config struct {
	GitHubURL       string
	ScaleSetName    string
	ProjectID       string
	Lane            string
	RunnerPrefix    string
	Profile         string
	ProvisionerSock string
	PATFile         string
	AppClientID     string
	AppInstallID    int64
	AppPrivateKey   string
	AdmissionV2     bool
	StateDir        string
}

type provisionRequest struct {
	SchemaVersion int    `json:"schema_version"`
	RequestID     string `json:"request_id"`
	ProjectID     string `json:"project_id"`
	Profile       string `json:"profile"`
	RunnerName    string `json:"runner_name"`
	JITConfig     string `json:"jit_config"`
}

type provisionRequestV2 struct {
	SchemaVersion int                   `json:"schema_version"`
	RequestID     string                `json:"request_id"`
	ProjectID     string                `json:"project_id"`
	WorkloadClass string                `json:"workload_class"`
	RunnerName    string                `json:"runner_name"`
	JITConfig     string                `json:"jit_config"`
	Attestation   controllerAttestation `json:"attestation"`
}

type provisionResponse struct {
	SchemaVersion int    `json:"schema_version"`
	Status        string `json:"status"`
	RequestID     string `json:"request_id,omitempty"`
	AdmissionID   string `json:"admission_id,omitempty"`
	ReceiptStatus string `json:"receipt_status,omitempty"`
	ErrorType     string `json:"error_type,omitempty"`
	Error         string `json:"error,omitempty"`
}

type provisionStatusRequest struct {
	SchemaVersion int    `json:"schema_version"`
	Operation     string `json:"operation"`
	RequestID     string `json:"request_id"`
}

type provisionStatusResponse struct {
	SchemaVersion int    `json:"schema_version"`
	Status        string `json:"status"`
	RequestID     string `json:"request_id"`
	RunnerName    string `json:"runner_name,omitempty"`
	AdmissionID   string `json:"admission_id,omitempty"`
	ErrorType     string `json:"error_type,omitempty"`
	Error         string `json:"error,omitempty"`
}

type scaleSetMaintenanceRequest struct {
	SchemaVersion      int    `json:"schema_version"`
	Operation          string `json:"operation"`
	ExpectedScaleSetID int    `json:"expected_scale_set_id"`
}

type scaleSetMaintenanceResponse struct {
	SchemaVersion int                            `json:"schema_version"`
	Status        string                         `json:"status"`
	ScaleSetID    int                            `json:"scale_set_id,omitempty"`
	ScaleSetName  string                         `json:"scale_set_name,omitempty"`
	Statistics    *scaleset.RunnerScaleSetStatistic `json:"statistics,omitempty"`
}

type scaleSetMaintenanceClient interface {
	GetRunnerScaleSet(context.Context, int, string) (*scaleset.RunnerScaleSet, error)
	DeleteRunnerScaleSet(context.Context, int) error
}

type runnerJITClient interface {
	GenerateJitRunnerConfig(
		context.Context,
		*scaleset.RunnerScaleSetJitRunnerSetting,
		int,
	) (*scaleset.RunnerScaleSetJitRunnerConfig, error)
	GetRunnerByName(context.Context, string) (*scaleset.RunnerReference, error)
	RemoveRunner(context.Context, int64) error
}

type pendingAdmissionJob struct {
	Metadata    scaleset.JobMessageBase
	Attestation controllerAttestation
	Workload    string
	RunnerName  string
}

type laneQuarantineReceipt struct {
	SchemaVersion        int    `json:"schema_version"`
	ReceiptID            string `json:"receipt_id"`
	Status               string `json:"status"`
	ProjectID            string `json:"project_id"`
	Lane                 string `json:"lane"`
	ScaleSetName         string `json:"scale_set_name"`
	ScaleSetID           int    `json:"scale_set_id"`
	TotalAssignedJobs    int    `json:"total_assigned_jobs"`
	ReconstructableJobs  int    `json:"reconstructable_jobs"`
	ActiveCount          int    `json:"active_count"`
	PendingCount         int    `json:"pending_count"`
	Reason               string `json:"reason"`
	ObservedAt           string `json:"observed_at"`
}

type laneResetPendingReceipt struct {
	SchemaVersion   int    `json:"schema_version"`
	ReceiptID       string `json:"receipt_id"`
	Status          string `json:"status"`
	ProjectID       string `json:"project_id"`
	Lane            string `json:"lane"`
	ScaleSetName    string `json:"scale_set_name"`
	ScaleSetID      int    `json:"scale_set_id"`
	OldScaleSetID   int    `json:"old_scale_set_id"`
	ResetGeneration string `json:"reset_generation"`
	ResetStartedAt  string `json:"reset_started_at"`
}

type recoveryZeroObservation struct {
	SchemaVersion   int    `json:"schema_version"`
	ResetGeneration string `json:"reset_generation"`
	ScaleSetID      int    `json:"scale_set_id"`
	ObservedAt      string `json:"observed_at"`
}

type scaler struct {
	mu              sync.Mutex
	active          map[string]string
	client          runnerJITClient
	sessionClient   listener.Client
	scaleSetID      int
	projectID       string
	lane            string
	profile         string
	scaleSetName    string
	runnerPrefix    string
	provisionerSock string
	stateDir        string
	admissionV2     bool
	attestor        jobAttestor
	pending             map[string]pendingAdmissionJob
	quarantined         bool
	quarantineID        string
	recoveryPending     bool
	resetGeneration     string
	resetOldScaleSetID  int
	resetPendingPath    string
	logger              *slog.Logger
}

func envOr(key, fallback string) string {
	if value := strings.TrimSpace(os.Getenv(key)); value != "" {
		return value
	}
	return fallback
}

func requiredEnv(key string) (string, error) {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return "", fmt.Errorf("%s is required", key)
	}
	return value, nil
}

func derivedControllerIdentity(projectID, lane string) (string, string, string, error) {
	if !projectIDPattern.MatchString(projectID) {
		return "", "", "", fmt.Errorf("project id rejected: %s", projectID)
	}
	switch lane {
	case "cpu":
		return "lambda-" + projectID, "lambda-" + projectID + "-", "cpu-test", nil
	case "gpu":
		return "lambda-" + projectID + "-gpu", "lambda-" + projectID + "-gpu-", "gpu-small", nil
	default:
		return "", "", "", fmt.Errorf("controller lane rejected: %s", lane)
	}
}

func workloadForDisplayClaim(displayName string) (string, error) {
	const prefix = "wc-admission-v1|workload="
	if !strings.HasPrefix(displayName, prefix) {
		return "", fmt.Errorf("job display claim has no admission workload")
	}
	rest := strings.TrimPrefix(displayName, prefix)
	workload, _, ok := strings.Cut(rest, "|")
	if !ok || !routeIDPattern.MatchString(workload) {
		return "", fmt.Errorf("job display claim workload is invalid")
	}
	return workload, nil
}

func loadConfig() (config, error) {
	githubURL, err := requiredEnv("WORKSPACE_CI_GITHUB_URL")
	if err != nil { return config{}, err }
	scaleSetName, err := requiredEnv("WORKSPACE_CI_SCALESET_NAME")
	if err != nil { return config{}, err }
	projectID, err := requiredEnv("WORKSPACE_CI_PROJECT_ID")
	if err != nil { return config{}, err }
	lane, err := requiredEnv("WORKSPACE_CI_LANE")
	if err != nil { return config{}, err }
	runnerPrefix, err := requiredEnv("WORKSPACE_CI_RUNNER_PREFIX")
	if err != nil { return config{}, err }

	expectedScaleSet, expectedPrefix, profile, err := derivedControllerIdentity(projectID, lane)
	if err != nil { return config{}, err }
	if scaleSetName != expectedScaleSet {
		return config{}, fmt.Errorf("controller scale-set does not match derived project/lane identity: got %s want %s", scaleSetName, expectedScaleSet)
	}
	if runnerPrefix != expectedPrefix {
		return config{}, fmt.Errorf("controller runner prefix does not match derived project/lane identity: got %s want %s", runnerPrefix, expectedPrefix)
	}

	stateRoot := envOr("WORKSPACE_CI_CONTROLLER_STATE_ROOT", defaultControllerStateRoot)
	if !filepath.IsAbs(stateRoot) {
		return config{}, fmt.Errorf("WORKSPACE_CI_CONTROLLER_STATE_ROOT must be absolute")
	}
	cfg := config{
		GitHubURL: githubURL, ScaleSetName: scaleSetName, ProjectID: projectID,
		Lane: lane, RunnerPrefix: runnerPrefix, Profile: profile,
		ProvisionerSock: envOr("WORKSPACE_CI_PROVISIONER_SOCKET", defaultProvisionerSock),
		PATFile: strings.TrimSpace(os.Getenv("WORKSPACE_CI_PAT_FILE")),
		AppClientID: strings.TrimSpace(os.Getenv("WORKSPACE_CI_APP_CLIENT_ID")),
		AppPrivateKey: strings.TrimSpace(os.Getenv("WORKSPACE_CI_APP_PRIVATE_KEY_FILE")),
		StateDir: filepath.Join(stateRoot, projectID+"-"+lane),
	}
	if raw := strings.TrimSpace(os.Getenv("WORKSPACE_CI_APP_INSTALLATION_ID")); raw != "" {
		value, err := strconv.ParseInt(raw, 10, 64)
		if err != nil || value <= 0 { return config{}, fmt.Errorf("invalid WORKSPACE_CI_APP_INSTALLATION_ID") }
		cfg.AppInstallID = value
	}
	switch raw := strings.TrimSpace(os.Getenv("WORKSPACE_CI_ADMISSION_V2_ENABLED")); raw {
	case "", "NO": cfg.AdmissionV2 = false
	case "YES": cfg.AdmissionV2 = true
	default: return config{}, fmt.Errorf("WORKSPACE_CI_ADMISSION_V2_ENABLED must be YES or NO")
	}
	hasApp := cfg.AppClientID != "" || cfg.AppInstallID != 0 || cfg.AppPrivateKey != ""
	if hasApp {
		if cfg.AppClientID == "" || cfg.AppInstallID == 0 || cfg.AppPrivateKey == "" {
			return config{}, fmt.Errorf("GitHub App credential configuration is incomplete")
		}
		if cfg.PATFile != "" { return config{}, fmt.Errorf("configure either GitHub App or PAT, not both") }
	} else if cfg.PATFile == "" {
		return config{}, fmt.Errorf("controller credential file is required")
	}
	return cfg, nil
}


func readSecretFile(path string) (string, error) {
	info, err := os.Stat(path)
	if err != nil {
		return "", err
	}
	if info.Mode().Perm()&0o077 != 0 {
		return "", fmt.Errorf("credential file %s must not be group/world accessible", path)
	}
	value, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	secret := strings.TrimSpace(string(value))
	if secret == "" {
		return "", fmt.Errorf("credential file %s is empty", path)
	}
	return secret, nil
}

func systemInfo(scaleSetID int) scaleset.SystemInfo {
	return scaleset.SystemInfo{
		System:     "workspace-control",
		Version:    "p5-v1",
		CommitSHA:  "e6daac702355cdb5b880b4fbdcf6d85dcd9e48e5",
		ScaleSetID: scaleSetID,
		Subsystem:  "lambda-ci-controller",
	}
}

func newScaleSetClient(cfg config) (*scaleset.Client, error) {
	if cfg.AppClientID != "" {
		privateKey, err := readSecretFile(cfg.AppPrivateKey)
		if err != nil {
			return nil, fmt.Errorf("read GitHub App private key: %w", err)
		}
		return scaleset.NewClientWithGitHubApp(
			scaleset.ClientWithGitHubAppConfig{
				GitHubConfigURL: cfg.GitHubURL,
				GitHubAppAuth: scaleset.GitHubAppAuth{
					ClientID:       cfg.AppClientID,
					InstallationID: cfg.AppInstallID,
					PrivateKey:     privateKey,
				},
				SystemInfo: systemInfo(0),
			},
		)
	}

	token, err := readSecretFile(cfg.PATFile)
	if err != nil {
		return nil, fmt.Errorf("read controller PAT: %w", err)
	}
	return scaleset.NewClientWithPersonalAccessToken(
		scaleset.NewClientWithPersonalAccessTokenConfig{
			GitHubConfigURL:     cfg.GitHubURL,
			PersonalAccessToken: token,
			SystemInfo:          systemInfo(0),
		},
	)
}

func ensureScaleSet(ctx context.Context, client *scaleset.Client, cfg config) (*scaleset.RunnerScaleSet, error) {
	const runnerGroupID = 1
	existing, err := client.GetRunnerScaleSet(ctx, runnerGroupID, cfg.ScaleSetName)
	if err != nil {
		return nil, fmt.Errorf("get runner scale set: %w", err)
	}
	if existing != nil {
		return existing, nil
	}

	created, err := client.CreateRunnerScaleSet(ctx, &scaleset.RunnerScaleSet{
		Name:          cfg.ScaleSetName,
		RunnerGroupID: runnerGroupID,
		Labels: []scaleset.Label{
			{Name: cfg.ScaleSetName},
		},
		RunnerSetting: scaleset.RunnerSetting{DisableUpdate: true},
	})
	if err != nil {
		return nil, fmt.Errorf("create runner scale set: %w", err)
	}
	return created, nil
}

func executeScaleSetMaintenance(
	ctx context.Context,
	client scaleSetMaintenanceClient,
	cfg config,
	request scaleSetMaintenanceRequest,
) (scaleSetMaintenanceResponse, error) {
	if request.SchemaVersion != 1 {
		return scaleSetMaintenanceResponse{}, fmt.Errorf("scale-set maintenance schema_version must be 1")
	}
	if request.Operation != "INSPECT" && request.Operation != "DELETE" {
		return scaleSetMaintenanceResponse{}, fmt.Errorf("scale-set maintenance operation is unsupported")
	}
	if request.ExpectedScaleSetID < 0 {
		return scaleSetMaintenanceResponse{}, fmt.Errorf("expected scale-set id is invalid")
	}
	const runnerGroupID = 1
	current, err := client.GetRunnerScaleSet(ctx, runnerGroupID, cfg.ScaleSetName)
	if err != nil {
		return scaleSetMaintenanceResponse{}, fmt.Errorf("inspect configured scale set: %w", err)
	}
	if current == nil {
		if request.Operation == "INSPECT" && request.ExpectedScaleSetID == 0 {
			return scaleSetMaintenanceResponse{
				SchemaVersion: 1,
				Status:        "MISSING",
				ScaleSetName:  cfg.ScaleSetName,
			}, nil
		}
		return scaleSetMaintenanceResponse{}, fmt.Errorf("configured scale set is missing")
	}
	if request.ExpectedScaleSetID > 0 && current.ID != request.ExpectedScaleSetID {
		return scaleSetMaintenanceResponse{}, fmt.Errorf(
			"scale-set id mismatch: got %d want %d",
			current.ID,
			request.ExpectedScaleSetID,
		)
	}
	response := scaleSetMaintenanceResponse{
		SchemaVersion: 1,
		Status:        "PRESENT",
		ScaleSetID:    current.ID,
		ScaleSetName:  current.Name,
		Statistics:    current.Statistics,
	}
	if request.Operation == "INSPECT" {
		return response, nil
	}
	if request.ExpectedScaleSetID <= 0 {
		return scaleSetMaintenanceResponse{}, fmt.Errorf("DELETE requires exact expected scale-set id")
	}
	if current.Statistics == nil {
		return scaleSetMaintenanceResponse{}, fmt.Errorf("scale-set statistics unavailable; refusing delete")
	}
	if current.Statistics.TotalRegisteredRunners != 0 ||
		current.Statistics.TotalBusyRunners != 0 ||
		current.Statistics.TotalRunningJobs != 0 {
		return scaleSetMaintenanceResponse{}, fmt.Errorf(
			"scale set is not quiescent: registered=%d busy=%d running=%d",
			current.Statistics.TotalRegisteredRunners,
			current.Statistics.TotalBusyRunners,
			current.Statistics.TotalRunningJobs,
		)
	}
	if err := client.DeleteRunnerScaleSet(ctx, current.ID); err != nil {
		return scaleSetMaintenanceResponse{}, fmt.Errorf("delete exact configured scale set: %w", err)
	}
	response.Status = "DELETED"
	return response, nil
}

func runScaleSetMaintenance(ctx context.Context, cfg config) error {
	client, err := newScaleSetClient(cfg)
	if err != nil {
		return err
	}
	decoder := json.NewDecoder(os.Stdin)
	var request scaleSetMaintenanceRequest
	if err := decoder.Decode(&request); err != nil {
		return fmt.Errorf("decode scale-set maintenance request: %w", err)
	}
	var extra any
	if err := decoder.Decode(&extra); err != io.EOF {
		if err == nil {
			return fmt.Errorf("scale-set maintenance accepts exactly one JSON object")
		}
		return fmt.Errorf("decode trailing scale-set maintenance input: %w", err)
	}
	response, err := executeScaleSetMaintenance(ctx, client, cfg, request)
	if err != nil {
		return err
	}
	encoder := json.NewEncoder(os.Stdout)
	return encoder.Encode(response)
}

func randomID() (string, error) {
	var raw [16]byte
	if _, err := rand.Read(raw[:]); err != nil {
		return "", err
	}
	raw[6] = (raw[6] & 0x0f) | 0x40
	raw[8] = (raw[8] & 0x3f) | 0x80
	hexed := hex.EncodeToString(raw[:])
	return fmt.Sprintf("%s-%s-%s-%s-%s", hexed[0:8], hexed[8:12], hexed[12:16], hexed[16:20], hexed[20:32]), nil
}

func runnerName(prefix string) (string, error) {
	if !strings.HasPrefix(prefix, "lambda-") || !strings.HasSuffix(prefix, "-") {
		return "", fmt.Errorf("runner-name prefix rejected: %s", prefix)
	}
	var raw [6]byte
	if _, err := rand.Read(raw[:]); err != nil { return "", err }
	return prefix + hex.EncodeToString(raw[:]), nil
}

func sendProvisionRequest(ctx context.Context, socketPath string, request any) (provisionResponse, error) {
	dialer := net.Dialer{Timeout: 5 * time.Second}
	conn, err := dialer.DialContext(ctx, "unix", socketPath)
	if err != nil {
		return provisionResponse{}, fmt.Errorf("connect provisioner: %w", err)
	}
	defer conn.Close()

	unixConn, ok := conn.(*net.UnixConn)
	if !ok {
		return provisionResponse{}, fmt.Errorf("provisioner connection is not Unix domain")
	}
	if err := json.NewEncoder(unixConn).Encode(request); err != nil {
		return provisionResponse{}, fmt.Errorf("write provision request: %w", err)
	}
	if err := unixConn.CloseWrite(); err != nil {
		return provisionResponse{}, fmt.Errorf("close provision request write side: %w", err)
	}

	var response provisionResponse
	if err := json.NewDecoder(unixConn).Decode(&response); err != nil {
		return provisionResponse{}, fmt.Errorf("read provision response: %w", err)
	}
	switch response.Status {
	case "ACCEPTED", "DUPLICATE", "BUSY":
		return response, nil
	case "REJECTED":
		return response, fmt.Errorf("provisioner rejected request: %s: %s", response.ErrorType, response.Error)
	default:
		return response, fmt.Errorf("unexpected provisioner status %q", response.Status)
	}
}

func sendProvisionStatusQuery(
	ctx context.Context,
	socketPath string,
	requestID string,
) (provisionStatusResponse, error) {
	dialer := net.Dialer{Timeout: 5 * time.Second}
	conn, err := dialer.DialContext(ctx, "unix", socketPath)
	if err != nil {
		return provisionStatusResponse{}, fmt.Errorf("connect provisioner status: %w", err)
	}
	defer conn.Close()

	unixConn, ok := conn.(*net.UnixConn)
	if !ok {
		return provisionStatusResponse{}, fmt.Errorf("provisioner status connection is not Unix domain")
	}
	request := provisionStatusRequest{
		SchemaVersion: 2,
		Operation:     "STATUS",
		RequestID:     requestID,
	}
	if err := json.NewEncoder(unixConn).Encode(request); err != nil {
		return provisionStatusResponse{}, fmt.Errorf("write provision status request: %w", err)
	}
	if err := unixConn.CloseWrite(); err != nil {
		return provisionStatusResponse{}, fmt.Errorf("close provision status write side: %w", err)
	}

	var response provisionStatusResponse
	if err := json.NewDecoder(unixConn).Decode(&response); err != nil {
		return provisionStatusResponse{}, fmt.Errorf("read provision status response: %w", err)
	}
	if response.RequestID != requestID {
		return provisionStatusResponse{}, fmt.Errorf(
			"provision status request id mismatch: got %q want %q",
			response.RequestID,
			requestID,
		)
	}
	switch response.Status {
	case "MISSING", "ACCEPTED", "COMPLETED", "FAILED":
		return response, nil
	case "REJECTED":
		return response, fmt.Errorf(
			"provisioner rejected status query: %s: %s",
			response.ErrorType,
			response.Error,
		)
	default:
		return response, fmt.Errorf("unexpected provision status %q", response.Status)
	}
}

func reconcileOrphanJITRegistration(
	ctx context.Context,
	client runnerJITClient,
	runnerName string,
	scaleSetID int,
) (bool, error) {
	existing, err := client.GetRunnerByName(ctx, runnerName)
	if err != nil {
		return false, fmt.Errorf("lookup deterministic runner registration: %w", err)
	}
	if existing == nil {
		return false, nil
	}
	if existing.Name != runnerName || existing.RunnerScaleSetID != scaleSetID {
		return false, fmt.Errorf(
			"deterministic runner registration mismatch name=%q scale_set_id=%d",
			existing.Name,
			existing.RunnerScaleSetID,
		)
	}
	if err := client.RemoveRunner(ctx, int64(existing.ID)); err != nil {
		return false, fmt.Errorf("remove orphaned deterministic runner registration: %w", err)
	}
	return true, nil
}

func (s *scaler) nextPendingAdmission() (string, pendingAdmissionJob, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var (
		selectedKey string
		selected    pendingAdmissionJob
		found       bool
	)
	for key, job := range s.pending {
		if !found ||
			job.Attestation.WorkflowRunID < selected.Attestation.WorkflowRunID ||
			(job.Attestation.WorkflowRunID == selected.Attestation.WorkflowRunID && key < selectedKey) {
			selectedKey = key
			selected = job
			found = true
		}
	}
	return selectedKey, selected, found
}

func (s *scaler) clearPendingRunner(runnerName string) {
	if runnerName == "" {
		return
	}
	for key, job := range s.pending {
		if job.RunnerName == runnerName {
			delete(s.pending, key)
		}
	}
}

func reconstructableAssignedCount(active, pending int) int {
	if pending > active {
		return pending
	}
	return active
}

func desiredRunnerTarget(
	stats *scaleset.RunnerScaleSetStatistic,
	pending int,
	active int,
	admissionV2 bool,
) int {
	target := 0
	if admissionV2 {
		// Admission-v2 execution authority comes only from locally tracked,
		// independently attested jobs. GitHub's aggregate assigned-job count is
		// diagnostic state and must never create a JIT/root grant by itself.
		target = reconstructableAssignedCount(active, pending)
	} else if stats != nil {
		target = stats.TotalAssignedJobs
	}
	if target > maxRunners {
		target = maxRunners
	}
	return target
}

func atomicWriteJSON(path string, value any) error {
	if !filepath.IsAbs(path) {
		return fmt.Errorf("state path must be absolute")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return fmt.Errorf("create state directory: %w", err)
	}
	raw, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal state: %w", err)
	}
	raw = append(raw, '\n')
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, raw, 0o600); err != nil {
		return fmt.Errorf("write state: %w", err)
	}
	if err := os.Chmod(tmp, 0o600); err != nil {
		_ = os.Remove(tmp)
		return fmt.Errorf("chmod state: %w", err)
	}
	if err := os.Rename(tmp, path); err != nil {
		_ = os.Remove(tmp)
		return fmt.Errorf("replace state: %w", err)
	}
	return nil
}

func (s *scaler) quarantinePath() string {
	return filepath.Join(s.stateDir, "quarantine.json")
}

func (s *scaler) loadQuarantine() error {
	raw, err := os.ReadFile(s.quarantinePath())
	if err == nil {
		var receipt laneQuarantineReceipt
		if err := json.Unmarshal(raw, &receipt); err != nil {
			return fmt.Errorf("parse controller quarantine: %w", err)
		}
		if receipt.SchemaVersion != 1 ||
			receipt.Status != "ASSIGNMENT_DIVERGENCE_QUARANTINED" ||
			receipt.ProjectID != s.projectID ||
			receipt.Lane != s.lane ||
			receipt.ScaleSetName != s.scaleSetName ||
			receipt.ScaleSetID != s.scaleSetID ||
			receipt.ReceiptID == "" {
			return fmt.Errorf("controller quarantine identity mismatch")
		}
		s.mu.Lock()
		s.quarantined = true
		s.quarantineID = receipt.ReceiptID
		s.mu.Unlock()
		return nil
	}
	if !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("read controller quarantine: %w", err)
	}

	pendingPaths, err := filepath.Glob(filepath.Join(s.stateDir, "reset-pending-*.json"))
	if err != nil {
		return fmt.Errorf("glob reset-pending state: %w", err)
	}
	if len(pendingPaths) == 0 {
		return nil
	}
	if len(pendingPaths) != 1 {
		return fmt.Errorf("multiple reset-pending receipts are present")
	}
	raw, err = os.ReadFile(pendingPaths[0])
	if err != nil {
		return fmt.Errorf("read reset-pending receipt: %w", err)
	}
	var pending laneResetPendingReceipt
	if err := json.Unmarshal(raw, &pending); err != nil {
		return fmt.Errorf("parse reset-pending receipt: %w", err)
	}
	oldID := pending.OldScaleSetID
	if oldID == 0 {
		oldID = pending.ScaleSetID
	}
	if pending.SchemaVersion != 1 ||
		pending.Status != "RECOVERY_SCALESET_RESET_PENDING" ||
		pending.ProjectID != s.projectID ||
		pending.Lane != s.lane ||
		pending.ScaleSetName != s.scaleSetName ||
		pending.ReceiptID == "" ||
		pending.ResetGeneration == "" ||
		oldID <= 0 ||
		oldID == s.scaleSetID {
		return fmt.Errorf("reset-pending controller identity mismatch")
	}
	s.mu.Lock()
	s.quarantined = true
	s.quarantineID = pending.ReceiptID
	s.recoveryPending = true
	s.resetGeneration = pending.ResetGeneration
	s.resetOldScaleSetID = oldID
	s.resetPendingPath = pendingPaths[0]
	s.mu.Unlock()
	return nil
}

func (s *scaler) persistAssignmentQuarantine(
	stats *scaleset.RunnerScaleSetStatistic,
	active int,
	pending int,
) error {
	if stats == nil {
		return fmt.Errorf("assignment divergence requires statistics")
	}
	s.mu.Lock()
	if s.quarantined {
		s.mu.Unlock()
		return nil
	}
	s.mu.Unlock()
	receiptID, err := randomID()
	if err != nil {
		return fmt.Errorf("create quarantine receipt id: %w", err)
	}
	receipt := laneQuarantineReceipt{
		SchemaVersion:       1,
		ReceiptID:           receiptID,
		Status:              "ASSIGNMENT_DIVERGENCE_QUARANTINED",
		ProjectID:           s.projectID,
		Lane:                s.lane,
		ScaleSetName:        s.scaleSetName,
		ScaleSetID:          s.scaleSetID,
		TotalAssignedJobs:   stats.TotalAssignedJobs,
		ReconstructableJobs: reconstructableAssignedCount(active, pending),
		ActiveCount:         active,
		PendingCount:        pending,
		Reason:              "github_assigned_count_exceeds_complete_reconstructable_jobs",
		ObservedAt:          time.Now().UTC().Format(time.RFC3339Nano),
	}
	if err := atomicWriteJSON(s.quarantinePath(), receipt); err != nil {
		return err
	}
	s.mu.Lock()
	s.quarantined = true
	s.quarantineID = receiptID
	s.mu.Unlock()
	s.logger.Error(
		"Admission-v2 lane quarantined on assignment divergence",
		slog.String("quarantine_receipt_id", receiptID),
		slog.Int("total_assigned_jobs", stats.TotalAssignedJobs),
		slog.Int("reconstructable_jobs", receipt.ReconstructableJobs),
	)
	return nil
}

func (s *scaler) resolveQuarantineFromCompleteMetadata(
	stats *scaleset.RunnerScaleSetStatistic,
	active int,
	pending int,
) error {
	if stats == nil || stats.TotalAssignedJobs <= 0 {
		return fmt.Errorf("quarantine cannot auto-resolve without assigned jobs")
	}
	reconstructable := reconstructableAssignedCount(active, pending)
	if reconstructable < stats.TotalAssignedJobs {
		return fmt.Errorf("quarantine remains ambiguous")
	}
	s.mu.Lock()
	receiptID := s.quarantineID
	s.mu.Unlock()
	resolved := map[string]any{
		"schema_version": 1,
		"receipt_id": receiptID,
		"status": "RESOLVED_BY_COMPLETE_METADATA",
		"project_id": s.projectID,
		"lane": s.lane,
		"scale_set_name": s.scaleSetName,
		"scale_set_id": s.scaleSetID,
		"total_assigned_jobs": stats.TotalAssignedJobs,
		"reconstructable_jobs": reconstructable,
		"resolved_at": time.Now().UTC().Format(time.RFC3339Nano),
	}
	if err := atomicWriteJSON(
		filepath.Join(s.stateDir, "resolved-"+receiptID+".json"),
		resolved,
	); err != nil {
		return err
	}
	if err := os.Remove(s.quarantinePath()); err != nil && !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("remove resolved quarantine: %w", err)
	}
	s.mu.Lock()
	s.quarantined = false
	s.quarantineID = ""
	s.mu.Unlock()
	s.logger.Info(
		"Admission-v2 quarantine resolved from complete authoritative metadata",
		slog.String("quarantine_receipt_id", receiptID),
	)
	return nil
}

func scaleSetStatisticsZero(stats *scaleset.RunnerScaleSetStatistic) bool {
	return stats != nil &&
		stats.TotalAvailableJobs == 0 &&
		stats.TotalAcquiredJobs == 0 &&
		stats.TotalAssignedJobs == 0 &&
		stats.TotalRunningJobs == 0 &&
		stats.TotalRegisteredRunners == 0 &&
		stats.TotalBusyRunners == 0 &&
		stats.TotalIdleRunners == 0
}

func (s *scaler) recoveryZeroPath() string {
	return filepath.Join(s.stateDir, "reset-zero-observation.json")
}

func (s *scaler) readyForSingleRetryPath() string {
	return filepath.Join(s.stateDir, "ready-for-single-retry.json")
}

func (s *scaler) observeResetPending(
	msg *scaleset.RunnerScaleSetMessage,
	active int,
	pending int,
) (bool, error) {
	s.mu.Lock()
	generation := s.resetGeneration
	oldScaleSetID := s.resetOldScaleSetID
	pendingPath := s.resetPendingPath
	receiptID := s.quarantineID
	s.mu.Unlock()
	if generation == "" || pendingPath == "" || receiptID == "" {
		return false, fmt.Errorf("reset-pending state is incomplete")
	}

	zero := scaleSetStatisticsZero(msg.Statistics) &&
		active == 0 &&
		pending == 0 &&
		len(msg.JobAvailableMessages) == 0 &&
		len(msg.JobAssignedMessages) == 0 &&
		len(msg.JobStartedMessages) == 0
	if !zero {
		if err := os.Remove(s.recoveryZeroPath()); err != nil && !errors.Is(err, os.ErrNotExist) {
			return false, fmt.Errorf("clear interrupted zero-state observation: %w", err)
		}
		return false, nil
	}

	now := time.Now().UTC()
	firstRaw, err := os.ReadFile(s.recoveryZeroPath())
	if errors.Is(err, os.ErrNotExist) {
		first := recoveryZeroObservation{
			SchemaVersion:   1,
			ResetGeneration: generation,
			ScaleSetID:      s.scaleSetID,
			ObservedAt:      now.Format(time.RFC3339Nano),
		}
		if err := atomicWriteJSON(s.recoveryZeroPath(), first); err != nil {
			return false, err
		}
		s.logger.Info(
			"Recorded first recovery zero-state observation",
			slog.String("reset_generation", generation),
			slog.Int("scale_set_id", s.scaleSetID),
		)
		return false, nil
	}
	if err != nil {
		return false, fmt.Errorf("read first recovery zero-state observation: %w", err)
	}
	var first recoveryZeroObservation
	if err := json.Unmarshal(firstRaw, &first); err != nil {
		return false, fmt.Errorf("parse first recovery zero-state observation: %w", err)
	}
	if first.SchemaVersion != 1 ||
		first.ResetGeneration != generation ||
		first.ScaleSetID != s.scaleSetID {
		return false, fmt.Errorf("recovery zero-state observation identity mismatch")
	}
	firstAt, err := time.Parse(time.RFC3339Nano, first.ObservedAt)
	if err != nil {
		return false, fmt.Errorf("parse first recovery zero-state timestamp: %w", err)
	}
	if now.Sub(firstAt) < 15*time.Second {
		return false, nil
	}

	ready := map[string]any{
		"schema_version": 1,
		"status": "READY_FOR_SINGLE_RETRY",
		"receipt_id": receiptID,
		"project_id": s.projectID,
		"lane": s.lane,
		"scale_set_name": s.scaleSetName,
		"old_scale_set_id": oldScaleSetID,
		"new_scale_set_id": s.scaleSetID,
		"reset_generation": generation,
		"first_zero_observed_at": first.ObservedAt,
		"second_zero_observed_at": now.Format(time.RFC3339Nano),
		"automatic_workflow_triggered": false,
	}
	if err := atomicWriteJSON(s.readyForSingleRetryPath(), ready); err != nil {
		return false, err
	}
	if err := os.Remove(pendingPath); err != nil {
		return false, fmt.Errorf("remove reset-pending receipt after ready proof: %w", err)
	}
	if err := os.Remove(s.recoveryZeroPath()); err != nil && !errors.Is(err, os.ErrNotExist) {
		return false, fmt.Errorf("remove recovery zero observation: %w", err)
	}
	s.mu.Lock()
	s.quarantined = false
	s.recoveryPending = false
	s.resetGeneration = ""
	s.resetOldScaleSetID = 0
	s.resetPendingPath = ""
	s.mu.Unlock()
	s.logger.Info(
		"Recovery reached READY_FOR_SINGLE_RETRY",
		slog.String("quarantine_receipt_id", receiptID),
		slog.String("reset_generation", generation),
		slog.Int("old_scale_set_id", oldScaleSetID),
		slog.Int("new_scale_set_id", s.scaleSetID),
	)
	return true, nil
}

func (s *scaler) consumeReadyForSingleRetry(
	attestation controllerAttestation,
) error {
	path := s.readyForSingleRetryPath()
	raw, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return fmt.Errorf("read recovery retry gate: %w", err)
	}
	var receipt map[string]any
	if err := json.Unmarshal(raw, &receipt); err != nil {
		return fmt.Errorf("parse recovery retry gate: %w", err)
	}
	status, _ := receipt["status"].(string)
	if status == "RECOVERY_RETRY_ACQUIRED" ||
		status == "RECOVERY_RETRY_COMPLETED" {
		return nil
	}
	if status != "READY_FOR_SINGLE_RETRY" {
		return fmt.Errorf("recovery retry gate status is invalid: %q", status)
	}
	if receipt["project_id"] != s.projectID ||
		receipt["lane"] != s.lane ||
		receipt["scale_set_name"] != s.scaleSetName {
		return fmt.Errorf("recovery retry gate identity mismatch")
	}
	newID, ok := receipt["new_scale_set_id"].(float64)
	if !ok || int(newID) != s.scaleSetID {
		return fmt.Errorf("recovery retry gate scale-set mismatch")
	}
	receipt["status"] = "RECOVERY_RETRY_ACQUIRED"
	receipt["job_id"] = attestation.JobID
	receipt["workflow_run_id"] = attestation.WorkflowRunID
	receipt["acquired_at"] = time.Now().UTC().Format(time.RFC3339Nano)
	receipt["automatic_workflow_triggered"] = false
	if err := atomicWriteJSON(path, receipt); err != nil {
		return fmt.Errorf("consume recovery retry gate: %w", err)
	}
	s.logger.Info(
		"Consumed recovery generation with first acquired job",
		slog.String("job_id", attestation.JobID),
		slog.Int64("workflow_run_id", attestation.WorkflowRunID),
	)
	return nil
}

func (s *scaler) completeRecoveryRetry(job *scaleset.JobCompleted) error {
	if job == nil || job.JobID == "" {
		return nil
	}
	path := s.readyForSingleRetryPath()
	raw, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return fmt.Errorf("read recovery retry receipt: %w", err)
	}
	var receipt map[string]any
	if err := json.Unmarshal(raw, &receipt); err != nil {
		return fmt.Errorf("parse recovery retry receipt: %w", err)
	}
	status, _ := receipt["status"].(string)
	if status == "RECOVERY_RETRY_COMPLETED" {
		return nil
	}
	if status != "RECOVERY_RETRY_ACQUIRED" {
		return nil
	}
	if receipt["job_id"] != job.JobID {
		return nil
	}
	receipt["status"] = "RECOVERY_RETRY_COMPLETED"
	receipt["result"] = job.Result
	receipt["runner_name"] = job.RunnerName
	receipt["completed_at"] = time.Now().UTC().Format(time.RFC3339Nano)
	if err := atomicWriteJSON(path, receipt); err != nil {
		return fmt.Errorf("complete recovery retry receipt: %w", err)
	}
	s.logger.Info(
		"Recovery retry reached terminal state",
		slog.String("job_id", job.JobID),
		slog.String("result", job.Result),
	)
	return nil
}

func recoveryMetadataComplete(job *scaleset.JobMessageBase) bool {
	return job != nil &&
		job.MessageType == scaleset.MessageTypeJobAssigned &&
		job.WorkflowRunID > 0 &&
		job.JobID != "" &&
		job.RepositoryName != "" &&
		job.OwnerName != "" &&
		job.JobWorkflowRef != "" &&
		job.JobDisplayName != "" &&
		job.EventName != ""
}

func (s *scaler) Scale(ctx context.Context, msg *scaleset.RunnerScaleSetMessage) error {
	if msg == nil {
		return nil
	}

	if s.admissionV2 {
		if s.attestor == nil {
			return fmt.Errorf("admission v2 enabled without GitHub attestor")
		}
		s.mu.Lock()
		recoveryPendingAtStart := s.recoveryPending
		s.mu.Unlock()
		// During reset-pending recovery, even complete lifecycle metadata is
		// observation-only until two durable zero-state observations prove a
		// fresh empty scale set. Do not reconstruct/acquire work in this mode.
		if !recoveryPendingAtStart {
		// Recover complete assigned-job identities before considering any new
		// JobAvailable acquisition. Sparse aggregate assigned state is never
		// execution authority.
		for _, assigned := range msg.JobAssignedMessages {
			s.mu.Lock()
			capacity := maxRunners - reconstructableAssignedCount(len(s.active), len(s.pending))
			s.mu.Unlock()
			if capacity <= 0 {
				continue
			}
			if !recoveryMetadataComplete(&assigned.JobMessageBase) {
				s.logger.Warn(
					"Incomplete JobAssigned recovery metadata is non-authoritative",
					slog.Int64("runner_request_id", assigned.RunnerRequestID),
					slog.Int64("workflow_run_id", assigned.WorkflowRunID),
					slog.Bool("job_id_present", assigned.JobID != ""),
					slog.Bool("workflow_ref_present", assigned.JobWorkflowRef != ""),
					slog.Bool("display_name_present", assigned.JobDisplayName != ""),
				)
				continue
			}
			workload, err := workloadForDisplayClaim(assigned.JobDisplayName)
			if err != nil {
				return fmt.Errorf("derive assigned workload: %w", err)
			}
			attestation, err := s.attestor.Attest(
				ctx,
				&assigned.JobMessageBase,
				s.scaleSetName,
				workload,
			)
			if err != nil {
				if errors.Is(err, errTerminalWorkflowJob) {
					s.logger.Info(
						"Ignoring terminal JobAssigned recovery metadata",
						slog.Int64("runner_request_id", assigned.RunnerRequestID),
						slog.Int64("workflow_run_id", assigned.WorkflowRunID),
						slog.String("reason", err.Error()),
					)
					continue
				}
				return fmt.Errorf("attest assigned job recovery metadata: %w", err)
			}
			jobKey := attestation.JobID
			s.mu.Lock()
			if _, exists := s.pending[jobKey]; !exists {
				s.pending[jobKey] = pendingAdmissionJob{
					Metadata:    assigned.JobMessageBase,
					Attestation: attestation,
					Workload:    workload,
				}
			}
			s.mu.Unlock()
			if err := s.consumeReadyForSingleRetry(attestation); err != nil {
				return fmt.Errorf("consume recovery retry on assigned recovery: %w", err)
			}
		}
		}
	}

	// Apply lifecycle state before divergence detection so completed work does
	// not look reconstructable and started work is represented by active state.
	s.mu.Lock()
	if s.admissionV2 {
		for _, started := range msg.JobStartedMessages {
			s.clearPendingRunner(started.RunnerName)
		}
	}
	for _, completed := range msg.JobCompletedMessages {
		delete(s.active, completed.RunnerName)
		if s.admissionV2 {
			s.clearPendingRunner(completed.RunnerName)
			if err := s.completeRecoveryRetry(completed); err != nil {
				s.mu.Unlock()
				return fmt.Errorf("complete recovery retry lifecycle: %w", err)
			}
		}
	}
	activeCount := len(s.active)
	pendingCount := len(s.pending)
	quarantined := s.quarantined
	quarantineID := s.quarantineID
	recoveryPending := s.recoveryPending
	s.mu.Unlock()

	if s.admissionV2 && recoveryPending {
		ready, err := s.observeResetPending(msg, activeCount, pendingCount)
		if err != nil {
			return fmt.Errorf("observe reset-pending zero state: %w", err)
		}
		if !ready {
			s.logger.Warn(
				"Admission-v2 lane remains reset-pending quarantined",
				slog.String("quarantine_receipt_id", quarantineID),
				slog.Int("scale_set_id", s.scaleSetID),
			)
		}
		// Even the second zero observation only opens the retry gate; never
		// acquire a job from the same message that transitions the state.
		return nil
	}

	if s.admissionV2 {
		reconstructable := reconstructableAssignedCount(activeCount, pendingCount)
		assignedReported := 0
		if msg.Statistics != nil {
			assignedReported = msg.Statistics.TotalAssignedJobs
		}
		if quarantined {
			// A quarantined lane may clear itself only when complete,
			// independently re-attested metadata reconstructs every currently
			// assigned job. A later aggregate zero alone is not sufficient.
			if assignedReported > 0 && reconstructable >= assignedReported {
				if err := s.resolveQuarantineFromCompleteMetadata(
					msg.Statistics,
					activeCount,
					pendingCount,
				); err != nil {
					return fmt.Errorf("resolve assignment quarantine: %w", err)
				}
			} else {
				s.logger.Warn(
					"Admission-v2 lane remains quarantined; refusing new acquisition",
					slog.String("quarantine_receipt_id", quarantineID),
					slog.Int("total_assigned_jobs", assignedReported),
					slog.Int("reconstructable_jobs", reconstructable),
				)
				return nil
			}
		} else if msg.Statistics != nil && assignedReported > reconstructable {
			if err := s.persistAssignmentQuarantine(
				msg.Statistics,
				activeCount,
				pendingCount,
			); err != nil {
				return fmt.Errorf("persist assignment quarantine: %w", err)
			}
			return nil
		}
	}

	if len(msg.JobAvailableMessages) > 0 {
		requestIDs := make([]int64, 0, len(msg.JobAvailableMessages))
		stagedKeys := make([]string, 0, len(msg.JobAvailableMessages))

		if s.admissionV2 {
			s.mu.Lock()
			capacity := maxRunners - reconstructableAssignedCount(len(s.active), len(s.pending))
			s.mu.Unlock()

			for _, job := range msg.JobAvailableMessages {
				if capacity <= 0 {
					break
				}
				workload, err := workloadForDisplayClaim(job.JobDisplayName)
				if err != nil {
					return fmt.Errorf("derive available workload: %w", err)
				}
				attestation, err := s.attestor.Attest(
					ctx,
					&job.JobMessageBase,
					s.scaleSetName,
					workload,
				)
				if err != nil {
					if errors.Is(err, errTerminalWorkflowJob) {
						s.logger.Info(
							"Ignoring terminal JobAvailable metadata",
							slog.Int64("runner_request_id", job.RunnerRequestID),
							slog.Int64("workflow_run_id", job.WorkflowRunID),
							slog.String("reason", err.Error()),
						)
						continue
					}
					return fmt.Errorf("attest available job before acquire: %w", err)
				}
				jobKey := attestation.JobID
				s.mu.Lock()
				if _, exists := s.pending[jobKey]; !exists {
					s.pending[jobKey] = pendingAdmissionJob{
						Metadata:    job.JobMessageBase,
						Attestation: attestation,
						Workload:    workload,
					}
					stagedKeys = append(stagedKeys, jobKey)
					requestIDs = append(requestIDs, job.RunnerRequestID)
					capacity--
				}
				s.mu.Unlock()
			}
		} else {
			for _, job := range msg.JobAvailableMessages {
				requestIDs = append(requestIDs, job.RunnerRequestID)
			}
		}

		if len(requestIDs) > 0 {
			if _, err := s.sessionClient.AcquireJobs(ctx, requestIDs); err != nil {
				if s.admissionV2 {
					s.mu.Lock()
					for _, jobKey := range stagedKeys {
						delete(s.pending, jobKey)
					}
					s.mu.Unlock()
				}
				return fmt.Errorf("acquire jobs: %w", err)
			}
			if s.admissionV2 {
				if len(stagedKeys) != 1 {
					return fmt.Errorf(
						"admission-v2 acquired unexpected staged job count: %d",
						len(stagedKeys),
					)
				}
				s.mu.Lock()
				acquired := s.pending[stagedKeys[0]]
				s.mu.Unlock()
				if err := s.consumeReadyForSingleRetry(acquired.Attestation); err != nil {
					return fmt.Errorf("consume recovery retry after acquire: %w", err)
				}
			}
		}
	}

	s.mu.Lock()
	current := len(s.active)
	pendingCount = len(s.pending)
	s.mu.Unlock()

	target := desiredRunnerTarget(msg.Statistics, pendingCount, current, s.admissionV2)
	if target <= 0 {
		s.mu.Lock()
		clear(s.active)
		if s.admissionV2 {
			clear(s.pending)
		}
		s.mu.Unlock()
		return nil
	}
	if current >= target {
		return nil
	}

	for current < target {
		var (
			name        string
			requestID   string
			workload    string
			attestation controllerAttestation
			pendingKey  string
			pendingJob  pendingAdmissionJob
			pendingOK   bool
			err         error
		)

		if s.admissionV2 {
			pendingKey, pendingJob, pendingOK = s.nextPendingAdmission()
			if !pendingOK {
				// This is intentionally non-authoritative even if aggregate
				// GitHub statistics still report an assigned job.
				s.logger.Info("Admission v2 waiting for complete pre-attested job metadata")
				return nil
			}
			attestation = pendingJob.Attestation
			workload = pendingJob.Workload
			if workload == "" {
				return fmt.Errorf("pending admission workload is missing")
			}
			requestID, name, err = deterministicAdmissionExecutionIDs(
				s.runnerPrefix,
				workload,
				attestation,
			)
			if err != nil {
				return fmt.Errorf("derive deterministic admission identity: %w", err)
			}
		} else {
			name, err = runnerName(s.runnerPrefix)
			if err != nil {
				return fmt.Errorf("runner name: %w", err)
			}
			requestID, err = randomID()
			if err != nil {
				return fmt.Errorf("request id: %w", err)
			}
		}

		if s.admissionV2 {
			status, err := sendProvisionStatusQuery(
				ctx,
				s.provisionerSock,
				requestID,
			)
			if err != nil {
				return fmt.Errorf("query durable provision state: %w", err)
			}
			switch status.Status {
			case "ACCEPTED":
				if status.RunnerName != name {
					return fmt.Errorf(
						"durable provision runner mismatch: got %q want %q",
						status.RunnerName,
						name,
					)
				}
				s.mu.Lock()
				s.active[name] = requestID
				if pendingOK {
					pendingJob.RunnerName = name
					s.pending[pendingKey] = pendingJob
				}
				s.mu.Unlock()
				s.logger.Info(
					"Recovered accepted durable provision state",
					slog.String("request_id", requestID),
					slog.String("runner_name", name),
					slog.String("admission_id", status.AdmissionID),
				)
				return nil
			case "COMPLETED", "FAILED":
				if status.RunnerName != "" && status.RunnerName != name {
					return fmt.Errorf(
						"terminal provision runner mismatch: got %q want %q",
						status.RunnerName,
						name,
					)
				}
				s.mu.Lock()
				if pendingOK {
					delete(s.pending, pendingKey)
				}
				s.mu.Unlock()
				s.logger.Info(
					"Recovered terminal durable provision state",
					slog.String("request_id", requestID),
					slog.String("runner_name", name),
					slog.String("receipt_status", status.Status),
					slog.String("admission_id", status.AdmissionID),
				)
				return nil
			case "MISSING":
				removed, err := reconcileOrphanJITRegistration(
					ctx,
					s.client,
					name,
					s.scaleSetID,
				)
				if err != nil {
					return err
				}
				if removed {
					s.logger.Info(
						"Removed orphaned JIT runner registration before regeneration",
						slog.String("request_id", requestID),
						slog.String("runner_name", name),
					)
				}
			default:
				return fmt.Errorf("unsupported durable provision state %q", status.Status)
			}
		}

		jit, err := s.client.GenerateJitRunnerConfig(
			ctx,
			&scaleset.RunnerScaleSetJitRunnerSetting{Name: name},
			s.scaleSetID,
		)
		if err != nil {
			return fmt.Errorf("generate JIT config: %w", err)
		}

		var request any
		if s.admissionV2 {
			request = provisionRequestV2{
				SchemaVersion: 2,
				RequestID:     requestID,
				ProjectID:     s.projectID,
				WorkloadClass: workload,
				RunnerName:    name,
				JITConfig:     jit.EncodedJITConfig,
				Attestation:   attestation,
			}
		} else {
			request = provisionRequest{
				SchemaVersion: 1,
				RequestID:     requestID,
				ProjectID:     s.projectID,
				Profile:       s.profile,
				RunnerName:    name,
				JITConfig:     jit.EncodedJITConfig,
			}
		}

		response, err := sendProvisionRequest(ctx, s.provisionerSock, request)
		if err != nil {
			return err
		}

		if response.Status == "BUSY" {
			if s.admissionV2 && jit.Runner != nil {
				if err := s.client.RemoveRunner(ctx, int64(jit.Runner.ID)); err != nil {
					return fmt.Errorf(
						"remove unconsumed JIT runner after BUSY: %w",
						err,
					)
				}
			}
			s.logger.Info(
				"Provisioner busy; removed unconsumed JIT registration and will retry",
				slog.String("request_id", requestID),
				slog.String("runner_name", name),
			)
			return nil
		}

		if s.admissionV2 && response.Status == "DUPLICATE" {
			switch response.ReceiptStatus {
			case "COMPLETED", "FAILED":
				s.mu.Lock()
				if pendingOK {
					delete(s.pending, pendingKey)
				}
				s.mu.Unlock()
				s.logger.Info(
					"Recovered terminal admission receipt without re-execution",
					slog.String("request_id", requestID),
					slog.String("receipt_status", response.ReceiptStatus),
					slog.String("admission_id", response.AdmissionID),
				)
				return nil
			}
		}

		s.mu.Lock()
		s.active[name] = requestID
		if s.admissionV2 && pendingOK {
			pendingJob.RunnerName = name
			s.pending[pendingKey] = pendingJob
		}
		current = len(s.active)
		s.mu.Unlock()

		s.logger.Info(
			"Provision request accepted",
			slog.String("request_id", requestID),
			slog.String("runner_name", name),
			slog.String("status", response.Status),
			slog.String("admission_id", response.AdmissionID),
		)
	}
	return nil
}

func runController(ctx context.Context, cfg config, logger *slog.Logger) error {
	client, err := newScaleSetClient(cfg)
	if err != nil {
		return err
	}
	scaleSet, err := ensureScaleSet(ctx, client, cfg)
	if err != nil {
		return err
	}
	client.SetSystemInfo(systemInfo(scaleSet.ID))

	hostname, err := os.Hostname()
	if err != nil || hostname == "" {
		hostname = "workspace-ci-controller"
	}
	sessionClient, err := client.MessageSessionClient(ctx, scaleSet.ID, hostname)
	if err != nil {
		return fmt.Errorf("create scale-set message session: %w", err)
	}
	defer sessionClient.Close(context.Background())

	l, err := listener.New(sessionClient, listener.Config{
		ScaleSetID: scaleSet.ID,
		MaxRunners: maxRunners,
		Logger:     logger.WithGroup("listener"),
	})
	if err != nil {
		return fmt.Errorf("create listener: %w", err)
	}

	var attestor jobAttestor
	if cfg.AdmissionV2 {
		attestor, err = newGitHubJobAttestor(cfg)
		if err != nil {
			return fmt.Errorf("create admission v2 GitHub attestor: %w", err)
		}
	}

	if err := os.MkdirAll(cfg.StateDir, 0o700); err != nil {
		return fmt.Errorf("create controller state directory: %w", err)
	}
	s := &scaler{
		active:          make(map[string]string),
		client:          client,
		sessionClient:   sessionClient,
		scaleSetID:      scaleSet.ID,
		projectID:       cfg.ProjectID,
		lane:            cfg.Lane,
		profile:         cfg.Profile,
		scaleSetName:    cfg.ScaleSetName,
		runnerPrefix:    cfg.RunnerPrefix,
		provisionerSock: cfg.ProvisionerSock,
		stateDir:        cfg.StateDir,
		admissionV2:     cfg.AdmissionV2,
		attestor:        attestor,
		pending:         make(map[string]pendingAdmissionJob),
		logger:          logger.WithGroup("scaler"),
	}
	if cfg.AdmissionV2 {
		if err := s.loadQuarantine(); err != nil {
			return fmt.Errorf("load controller quarantine state: %w", err)
		}
	}

	logger.Info(
		"Starting Lambda CI scale-set listener",
		slog.Int("scale_set_id", scaleSet.ID),
		slog.String("scale_set_name", cfg.ScaleSetName),
		slog.Int("max_runners", maxRunners),
		slog.Bool("admission_v2", cfg.AdmissionV2),
		slog.String("controller_state_dir", cfg.StateDir),
		slog.Bool("quarantined", s.quarantined),
	)

	if err := l.Run(ctx, s); !errors.Is(err, context.Canceled) {
		return fmt.Errorf("listener stopped: %w", err)
	}
	return nil
}

func main() {
	cfg, err := loadConfig()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	if len(os.Args) == 2 && os.Args[1] == "--scale-set-maintenance" {
		if err := runScaleSetMaintenance(ctx, cfg); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		return
	}

	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	if err := runController(ctx, cfg, logger); err != nil {
		logger.Error("controller exited", slog.String("error", err.Error()))
		os.Exit(1)
	}
}

func init() {
	// Reject surprising relative credential/socket paths at process start.
	for _, key := range []string{"WORKSPACE_CI_PAT_FILE", "WORKSPACE_CI_APP_PRIVATE_KEY_FILE"} {
		if value := strings.TrimSpace(os.Getenv(key)); value != "" && !filepath.IsAbs(value) {
			panic(key + " must be an absolute path")
		}
	}
}
