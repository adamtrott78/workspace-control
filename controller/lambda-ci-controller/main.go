package main

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/actions/scaleset"
	"github.com/actions/scaleset/listener"
)

const (
	defaultGitHubURL      = "https://github.com/adamtrott78/research-engine"
	defaultScaleSetName    = "lambda-research-engine"
	gpuScaleSetName        = "lambda-research-engine-gpu"
	defaultProjectID       = "research-engine"
	defaultProfile         = "cpu-test"
	gpuProfile             = "gpu-small"
	modelEvalWorkload      = "model-eval-single-gpu"
	defaultProvisionerSock = "/run/workspace-ci/provisioner.sock"
	maxRunners             = 1
)

type config struct {
	GitHubURL       string
	ScaleSetName    string
	ProjectID       string
	Profile         string
	ProvisionerSock string
	PATFile         string
	AppClientID     string
	AppInstallID    int64
	AppPrivateKey   string
	AdmissionV2     bool
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

type scaler struct {
	mu              sync.Mutex
	active          map[string]string
	client          runnerJITClient
	sessionClient   listener.Client
	scaleSetID      int
	projectID       string
	profile         string
	scaleSetName    string
	provisionerSock string
	admissionV2     bool
	attestor        jobAttestor
	pending         map[string]pendingAdmissionJob
	logger          *slog.Logger
}

func envOr(key, fallback string) string {
	if value := strings.TrimSpace(os.Getenv(key)); value != "" {
		return value
	}
	return fallback
}

func controllerMappingAllowed(scaleSetName, profile string) bool {
	return (scaleSetName == defaultScaleSetName && profile == defaultProfile) ||
		(scaleSetName == gpuScaleSetName && profile == gpuProfile)
}

func workloadForDisplayClaim(profile, displayName string) (string, error) {
	const prefix = "wc-admission-v1|workload="
	if !strings.HasPrefix(displayName, prefix) {
		return "", fmt.Errorf("job display claim has no admission workload")
	}
	rest := strings.TrimPrefix(displayName, prefix)
	workload, _, ok := strings.Cut(rest, "|")
	if !ok || workload == "" {
		return "", fmt.Errorf("job display claim workload is incomplete")
	}
	switch profile {
	case defaultProfile:
		if workload != defaultProfile {
			return "", fmt.Errorf("CPU controller workload rejected: %s", workload)
		}
	case gpuProfile:
		if workload != gpuProfile && workload != modelEvalWorkload {
			return "", fmt.Errorf("GPU controller workload rejected: %s", workload)
		}
	default:
		return "", fmt.Errorf("controller profile rejected: %s", profile)
	}
	return workload, nil
}

func loadConfig() (config, error) {
	cfg := config{
		GitHubURL:       envOr("WORKSPACE_CI_GITHUB_URL", defaultGitHubURL),
		ScaleSetName:    envOr("WORKSPACE_CI_SCALESET_NAME", defaultScaleSetName),
		ProjectID:       envOr("WORKSPACE_CI_PROJECT_ID", defaultProjectID),
		Profile:         envOr("WORKSPACE_CI_PROFILE", defaultProfile),
		ProvisionerSock: envOr("WORKSPACE_CI_PROVISIONER_SOCKET", defaultProvisionerSock),
		PATFile:         strings.TrimSpace(os.Getenv("WORKSPACE_CI_PAT_FILE")),
		AppClientID:     strings.TrimSpace(os.Getenv("WORKSPACE_CI_APP_CLIENT_ID")),
		AppPrivateKey:   strings.TrimSpace(os.Getenv("WORKSPACE_CI_APP_PRIVATE_KEY_FILE")),
	}

	if raw := strings.TrimSpace(os.Getenv("WORKSPACE_CI_APP_INSTALLATION_ID")); raw != "" {
		value, err := strconv.ParseInt(raw, 10, 64)
		if err != nil || value <= 0 {
			return config{}, fmt.Errorf("invalid WORKSPACE_CI_APP_INSTALLATION_ID")
		}
		cfg.AppInstallID = value
	}

	switch raw := strings.TrimSpace(os.Getenv("WORKSPACE_CI_ADMISSION_V2_ENABLED")); raw {
	case "", "NO":
		cfg.AdmissionV2 = false
	case "YES":
		cfg.AdmissionV2 = true
	default:
		return config{}, fmt.Errorf(
			"WORKSPACE_CI_ADMISSION_V2_ENABLED must be YES or NO",
		)
	}

	if cfg.ProjectID != defaultProjectID {
		return config{}, fmt.Errorf("P5 pilot project is fixed to %s", defaultProjectID)
	}
	if !controllerMappingAllowed(cfg.ScaleSetName, cfg.Profile) {
		return config{}, fmt.Errorf(
			"P5 controller scale-set/profile mapping rejected: %s/%s",
			cfg.ScaleSetName,
			cfg.Profile,
		)
	}

	hasApp := cfg.AppClientID != "" || cfg.AppInstallID != 0 || cfg.AppPrivateKey != ""
	if hasApp {
		if cfg.AppClientID == "" || cfg.AppInstallID == 0 || cfg.AppPrivateKey == "" {
			return config{}, fmt.Errorf("GitHub App credential configuration is incomplete")
		}
		if cfg.PATFile != "" {
			return config{}, fmt.Errorf("configure either GitHub App or PAT, not both")
		}
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

func runnerName(profile string) (string, error) {
	var prefix string
	switch profile {
	case defaultProfile:
		prefix = "lambda-research-engine-"
	case gpuProfile:
		prefix = "lambda-research-engine-gpu-"
	default:
		return "", fmt.Errorf("runner-name profile rejected: %s", profile)
	}
	var raw [6]byte
	if _, err := rand.Read(raw[:]); err != nil {
		return "", err
	}
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

func desiredRunnerTarget(stats *scaleset.RunnerScaleSetStatistic, pending int) int {
	target := 0
	if stats != nil {
		target = stats.TotalAssignedJobs
	}
	if pending > target {
		target = pending
	}
	if target > maxRunners {
		target = maxRunners
	}
	return target
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

	if len(msg.JobAvailableMessages) > 0 {
		requestIDs := make([]int64, 0, len(msg.JobAvailableMessages))
		stagedKeys := make([]string, 0, len(msg.JobAvailableMessages))

		if s.admissionV2 {
			if s.attestor == nil {
				return fmt.Errorf("admission v2 enabled without GitHub attestor")
			}

			s.mu.Lock()
			capacity := maxRunners - len(s.active) - len(s.pending)
			s.mu.Unlock()

			for _, job := range msg.JobAvailableMessages {
				if capacity <= 0 {
					break
				}
				workload, err := workloadForDisplayClaim(
					s.profile,
					job.JobDisplayName,
				)
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
		}
	}

	if s.admissionV2 {
		if s.attestor == nil {
			return fmt.Errorf("admission v2 enabled without GitHub attestor")
		}
		for _, assigned := range msg.JobAssignedMessages {
			s.mu.Lock()
			capacity := maxRunners - len(s.active) - len(s.pending)
			s.mu.Unlock()
			if capacity <= 0 {
				continue
			}
			if !recoveryMetadataComplete(&assigned.JobMessageBase) {
				s.logger.Warn(
					"Ignoring incomplete JobAssigned recovery metadata",
					slog.Int64("runner_request_id", assigned.RunnerRequestID),
					slog.Int64("workflow_run_id", assigned.WorkflowRunID),
					slog.Bool("job_id_present", assigned.JobID != ""),
					slog.Bool("workflow_ref_present", assigned.JobWorkflowRef != ""),
					slog.Bool("display_name_present", assigned.JobDisplayName != ""),
				)
				continue
			}
			workload, err := workloadForDisplayClaim(
				s.profile,
				assigned.JobDisplayName,
			)
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
		}
	}

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
		}
	}
	current := len(s.active)
	pendingCount := len(s.pending)
	s.mu.Unlock()

	target := desiredRunnerTarget(msg.Statistics, pendingCount)
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
				s.logger.Info("Admission v2 waiting for pre-attested job metadata")
				return nil
			}
			attestation = pendingJob.Attestation
			workload = pendingJob.Workload
			if workload == "" {
				return fmt.Errorf("pending admission workload is missing")
			}
			requestID, name, err = deterministicAdmissionExecutionIDs(
				workload,
				attestation,
			)
			if err != nil {
				return fmt.Errorf("derive deterministic admission identity: %w", err)
			}
		} else {
			name, err = runnerName(s.profile)
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
		// Keep canonical pending admission identity until JobStarted so
		// lifecycle-specific runnerRequestId omissions or reassignments cannot
		// create a second root grant for the same verified workflow job.
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

	s := &scaler{
		active:          make(map[string]string),
		client:          client,
		sessionClient:   sessionClient,
		scaleSetID:      scaleSet.ID,
		projectID:       cfg.ProjectID,
		profile:         cfg.Profile,
		scaleSetName:    cfg.ScaleSetName,
		provisionerSock: cfg.ProvisionerSock,
		admissionV2:     cfg.AdmissionV2,
		attestor:        attestor,
		pending:         make(map[string]pendingAdmissionJob),
		logger:          logger.WithGroup("scaler"),
	}

	logger.Info(
		"Starting Lambda CI scale-set listener",
		slog.Int("scale_set_id", scaleSet.ID),
		slog.String("scale_set_name", cfg.ScaleSetName),
		slog.Int("max_runners", maxRunners),
		slog.Bool("admission_v2", cfg.AdmissionV2),
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
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

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
