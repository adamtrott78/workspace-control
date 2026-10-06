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
	defaultScaleSetName   = "lambda-research-engine"
	defaultProjectID      = "research-engine"
	defaultProfile        = "cpu-test"
	defaultProvisionerSock = "/run/workspace-ci/provisioner.sock"
	maxRunners            = 1
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
}

type provisionRequest struct {
	SchemaVersion int    `json:"schema_version"`
	RequestID     string `json:"request_id"`
	ProjectID     string `json:"project_id"`
	Profile       string `json:"profile"`
	RunnerName    string `json:"runner_name"`
	JITConfig     string `json:"jit_config"`
}

type provisionResponse struct {
	SchemaVersion int    `json:"schema_version"`
	Status        string `json:"status"`
	RequestID     string `json:"request_id,omitempty"`
	ErrorType     string `json:"error_type,omitempty"`
	Error         string `json:"error,omitempty"`
}

type scaler struct {
	mu              sync.Mutex
	active          map[string]string
	client          *scaleset.Client
	sessionClient   listener.Client
	scaleSetID      int
	projectID       string
	profile         string
	provisionerSock string
	logger          *slog.Logger
}

func envOr(key, fallback string) string {
	if value := strings.TrimSpace(os.Getenv(key)); value != "" {
		return value
	}
	return fallback
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

	if cfg.ProjectID != defaultProjectID {
		return config{}, fmt.Errorf("P5 pilot project is fixed to %s", defaultProjectID)
	}
	if cfg.Profile != defaultProfile {
		return config{}, fmt.Errorf("P5 pilot profile is fixed to %s", defaultProfile)
	}
	if cfg.ScaleSetName != defaultScaleSetName {
		return config{}, fmt.Errorf("P5 pilot scale set is fixed to %s", defaultScaleSetName)
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

func runnerName() (string, error) {
	var raw [6]byte
	if _, err := rand.Read(raw[:]); err != nil {
		return "", err
	}
	return "lambda-research-engine-" + hex.EncodeToString(raw[:]), nil
}

func sendProvisionRequest(ctx context.Context, socketPath string, request provisionRequest) (provisionResponse, error) {
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

func (s *scaler) Scale(ctx context.Context, msg *scaleset.RunnerScaleSetMessage) error {
	if msg == nil {
		return nil
	}

	if len(msg.JobAvailableMessages) > 0 {
		requestIDs := make([]int64, 0, len(msg.JobAvailableMessages))
		for _, job := range msg.JobAvailableMessages {
			requestIDs = append(requestIDs, job.RunnerRequestID)
		}
		if _, err := s.sessionClient.AcquireJobs(ctx, requestIDs); err != nil {
			return fmt.Errorf("acquire jobs: %w", err)
		}
	}

	s.mu.Lock()
	for _, completed := range msg.JobCompletedMessages {
		delete(s.active, completed.RunnerName)
	}
	current := len(s.active)
	s.mu.Unlock()

	if msg.Statistics == nil {
		return nil
	}
	target := msg.Statistics.TotalAssignedJobs
	if target > maxRunners {
		target = maxRunners
	}
	if target <= 0 {
		s.mu.Lock()
		clear(s.active)
		s.mu.Unlock()
		return nil
	}
	if current >= target {
		return nil
	}

	for current < target {
		name, err := runnerName()
		if err != nil {
			return fmt.Errorf("runner name: %w", err)
		}
		jit, err := s.client.GenerateJitRunnerConfig(
			ctx,
			&scaleset.RunnerScaleSetJitRunnerSetting{Name: name},
			s.scaleSetID,
		)
		if err != nil {
			return fmt.Errorf("generate JIT config: %w", err)
		}
		requestID, err := randomID()
		if err != nil {
			return fmt.Errorf("request id: %w", err)
		}

		response, err := sendProvisionRequest(ctx, s.provisionerSock, provisionRequest{
			SchemaVersion: 1,
			RequestID:     requestID,
			ProjectID:     s.projectID,
			Profile:       s.profile,
			RunnerName:    name,
			JITConfig:     jit.EncodedJITConfig,
		})
		if err != nil {
			return err
		}

		s.mu.Lock()
		if response.Status == "BUSY" {
			// Max-capacity=1 means BUSY represents already-provisioned capacity
			// during controller restart/recovery. Track a sentinel until stats fall.
			s.active["__provisioner_busy__"] = requestID
		} else {
			s.active[name] = requestID
		}
		current = len(s.active)
		s.mu.Unlock()

		s.logger.Info(
			"Provision request accepted",
			slog.String("request_id", requestID),
			slog.String("runner_name", name),
			slog.String("status", response.Status),
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

	s := &scaler{
		active:          make(map[string]string),
		client:          client,
		sessionClient:   sessionClient,
		scaleSetID:      scaleSet.ID,
		projectID:       cfg.ProjectID,
		profile:         cfg.Profile,
		provisionerSock: cfg.ProvisionerSock,
		logger:          logger.WithGroup("scaler"),
	}

	logger.Info(
		"Starting Lambda CI scale-set listener",
		slog.Int("scale_set_id", scaleSet.ID),
		slog.String("scale_set_name", cfg.ScaleSetName),
		slog.Int("max_runners", maxRunners),
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
