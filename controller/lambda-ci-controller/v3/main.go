package main

import (
	"context"
	"crypto/rsa"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/actions/scaleset"
	"github.com/actions/scaleset/listener"
	"github.com/golang-jwt/jwt/v5"
)

const githubAPIVersion = "2022-11-28"

type runtimeConfig struct {
	PolicyPath      string
	ProvisionerSock string
	StateRoot       string
	PATFile         string
	AppClientID     string
	AppInstallID    int64
	AppPrivateKey   string
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

func loadRuntimeConfig() (runtimeConfig, error) {
	policyPath, err := requiredEnv("WORKSPACE_CI_V3_CONTROLLER_POLICY")
	if err != nil {
		return runtimeConfig{}, err
	}
	cfg := runtimeConfig{
		PolicyPath:      policyPath,
		ProvisionerSock: envOr("WORKSPACE_CI_V3_PROVISIONER_SOCKET", defaultV3ProvisionerSocket),
		StateRoot:       envOr("WORKSPACE_CI_V3_CONTROLLER_STATE_ROOT", defaultV3StateRoot),
		PATFile:         strings.TrimSpace(os.Getenv("WORKSPACE_CI_PAT_FILE")),
		AppClientID:     strings.TrimSpace(os.Getenv("WORKSPACE_CI_APP_CLIENT_ID")),
		AppPrivateKey:   strings.TrimSpace(os.Getenv("WORKSPACE_CI_APP_PRIVATE_KEY_FILE")),
	}
	if !filepath.IsAbs(cfg.PolicyPath) ||
		!filepath.IsAbs(cfg.ProvisionerSock) ||
		!filepath.IsAbs(cfg.StateRoot) {
		return runtimeConfig{}, fmt.Errorf("v3 policy/socket/state paths must be absolute")
	}
	if raw := strings.TrimSpace(os.Getenv("WORKSPACE_CI_APP_INSTALLATION_ID")); raw != "" {
		value, err := parsePositiveInt64(raw, "WORKSPACE_CI_APP_INSTALLATION_ID")
		if err != nil {
			return runtimeConfig{}, err
		}
		cfg.AppInstallID = value
	}
	hasApp := cfg.AppClientID != "" || cfg.AppInstallID != 0 || cfg.AppPrivateKey != ""
	if hasApp {
		if cfg.AppClientID == "" || cfg.AppInstallID <= 0 || cfg.AppPrivateKey == "" {
			return runtimeConfig{}, fmt.Errorf("GitHub App credential configuration is incomplete")
		}
		if cfg.PATFile != "" {
			return runtimeConfig{}, fmt.Errorf("configure either GitHub App or PAT, not both")
		}
	} else if cfg.PATFile == "" {
		return runtimeConfig{}, fmt.Errorf("controller credential file is required")
	}
	return cfg, nil
}

func readSecretFile(path string) (string, error) {
	info, err := os.Stat(path)
	if err != nil {
		return "", err
	}
	perm := info.Mode().Perm()
	// V3 class users intentionally share only their repository-scoped
	// credential group. Allow owner read/write plus optional group read, but
	// reject owner execute, group write/execute, and every world permission.
	if perm&0o137 != 0 || perm&0o440 == 0 {
		return "", fmt.Errorf(
			"credential file %s must be owner-readable with at most read-only group access",
			path,
		)
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	value := strings.TrimSpace(string(raw))
	if value == "" {
		return "", fmt.Errorf("credential file %s is empty", path)
	}
	return value, nil
}

func repositoryURL(repository string) (string, error) {
	parts := strings.Split(repository, "/")
	if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
		return "", fmt.Errorf("controller policy repository must be owner/name")
	}
	return "https://github.com/" + repository, nil
}

func systemInfo(scaleSetID int) scaleset.SystemInfo {
	return scaleset.SystemInfo{
		System:     "workspace-control",
		Version:    "v3",
		CommitSHA:  "e6daac702355cdb5b880b4fbdcf6d85dcd9e48e5",
		ScaleSetID: scaleSetID,
		Subsystem:  "lambda-ci-controller-v3",
	}
}

func newScaleSetClient(cfg runtimeConfig, policy controllerPolicy) (*scaleset.Client, error) {
	githubURL, err := repositoryURL(policy.Repository)
	if err != nil {
		return nil, err
	}
	if cfg.AppClientID != "" {
		privateKey, err := readSecretFile(cfg.AppPrivateKey)
		if err != nil {
			return nil, fmt.Errorf("read GitHub App private key: %w", err)
		}
		return scaleset.NewClientWithGitHubApp(
			scaleset.ClientWithGitHubAppConfig{
				GitHubConfigURL: githubURL,
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
			GitHubConfigURL:     githubURL,
			PersonalAccessToken: token,
			SystemInfo:          systemInfo(0),
		},
	)
}

func requireScaleSet(
	ctx context.Context,
	client *scaleset.Client,
	policy controllerPolicy,
) (*scaleset.RunnerScaleSet, error) {
	const runnerGroupID = 1
	scaleSet, err := client.GetRunnerScaleSet(ctx, runnerGroupID, policy.ScaleSetName)
	if err != nil {
		return nil, fmt.Errorf("get exact v3 runner scale set: %w", err)
	}
	if scaleSet == nil {
		return nil, fmt.Errorf(
			"v3 runner scale set %q is missing; reconciliation must create it before controller activation",
			policy.ScaleSetName,
		)
	}
	if scaleSet.Name != policy.ScaleSetName {
		return nil, fmt.Errorf("v3 scale-set identity mismatch")
	}
	return scaleSet, nil
}

type tokenSource interface {
	Token(context.Context) (string, error)
}

type fixedTokenSource string

func (s fixedTokenSource) Token(context.Context) (string, error) {
	if strings.TrimSpace(string(s)) == "" {
		return "", fmt.Errorf("REST token is empty")
	}
	return string(s), nil
}

type appTokenSource struct {
	clientID       string
	installationID int64
	privateKey     *rsa.PrivateKey
	apiBase        string
	httpClient     *http.Client
	token          string
	expiresAt      time.Time
}

func newAppTokenSource(
	clientID string,
	installationID int64,
	privateKeyPEM string,
	httpClient *http.Client,
) (*appTokenSource, error) {
	key, err := jwt.ParseRSAPrivateKeyFromPEM([]byte(privateKeyPEM))
	if err != nil {
		return nil, fmt.Errorf("parse GitHub App private key: %w", err)
	}
	return &appTokenSource{
		clientID:       clientID,
		installationID: installationID,
		privateKey:     key,
		apiBase:        "https://api.github.com",
		httpClient:     httpClient,
	}, nil
}

func (s *appTokenSource) Token(ctx context.Context) (string, error) {
	now := time.Now().UTC()
	if s.token != "" && now.Add(time.Minute).Before(s.expiresAt) {
		return s.token, nil
	}
	claims := jwt.RegisteredClaims{
		Issuer:    s.clientID,
		IssuedAt:  jwt.NewNumericDate(now.Add(-time.Minute)),
		ExpiresAt: jwt.NewNumericDate(now.Add(8 * time.Minute)),
	}
	appJWT, err := jwt.NewWithClaims(jwt.SigningMethodRS256, claims).SignedString(s.privateKey)
	if err != nil {
		return "", fmt.Errorf("sign GitHub App JWT: %w", err)
	}
	endpoint := fmt.Sprintf(
		"%s/app/installations/%d/access_tokens",
		s.apiBase,
		s.installationID,
	)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("Authorization", "Bearer "+appJWT)
	req.Header.Set("X-GitHub-Api-Version", githubAPIVersion)
	resp, err := s.httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusCreated {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return "", fmt.Errorf(
			"GitHub App installation token status=%d body=%q",
			resp.StatusCode,
			strings.TrimSpace(string(body)),
		)
	}
	var payload struct {
		Token     string    `json:"token"`
		ExpiresAt time.Time `json:"expires_at"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return "", err
	}
	if payload.Token == "" || payload.ExpiresAt.IsZero() {
		return "", fmt.Errorf("GitHub App installation token response incomplete")
	}
	s.token = payload.Token
	s.expiresAt = payload.ExpiresAt.UTC()
	return s.token, nil
}

type githubVerifier struct {
	policy     controllerPolicy
	owner      string
	repo       string
	apiBase    string
	httpClient *http.Client
	tokens     tokenSource
	logger     *slog.Logger
}

func newGitHubVerifier(
	cfg runtimeConfig,
	policy controllerPolicy,
	logger *slog.Logger,
) (*githubVerifier, error) {
	parts := strings.Split(policy.Repository, "/")
	if len(parts) != 2 {
		return nil, fmt.Errorf("policy repository invalid")
	}
	httpClient := &http.Client{Timeout: 15 * time.Second}
	var tokens tokenSource
	if cfg.AppClientID != "" {
		privateKey, err := readSecretFile(cfg.AppPrivateKey)
		if err != nil {
			return nil, err
		}
		source, err := newAppTokenSource(
			cfg.AppClientID,
			cfg.AppInstallID,
			privateKey,
			httpClient,
		)
		if err != nil {
			return nil, err
		}
		tokens = source
	} else {
		token, err := readSecretFile(cfg.PATFile)
		if err != nil {
			return nil, err
		}
		tokens = fixedTokenSource(token)
	}
	return &githubVerifier{
		policy:     policy,
		owner:      parts[0],
		repo:       parts[1],
		apiBase:    "https://api.github.com",
		httpClient: httpClient,
		tokens:     tokens,
		logger:     logger,
	}, nil
}

func (v *githubVerifier) getJSON(ctx context.Context, path string, target any) error {
	for attempt := 0; ; attempt++ {
		token, err := v.tokens.Token(ctx)
		if err != nil {
			return err
		}
		req, err := http.NewRequestWithContext(
			ctx,
			http.MethodGet,
			strings.TrimRight(v.apiBase, "/")+path,
			nil,
		)
		if err != nil {
			return err
		}
		req.Header.Set("Accept", "application/vnd.github+json")
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("X-GitHub-Api-Version", githubAPIVersion)
		resp, err := v.httpClient.Do(req)
		if err == nil && resp.StatusCode == http.StatusOK {
			defer resp.Body.Close()
			return json.NewDecoder(resp.Body).Decode(target)
		}
		if err == nil && resp != nil {
			body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
			resp.Body.Close()
			if resp.StatusCode != http.StatusTooManyRequests && resp.StatusCode < 500 {
				return fmt.Errorf(
					"GitHub REST status=%d path=%s body=%q",
					resp.StatusCode,
					path,
					strings.TrimSpace(string(body)),
				)
			}
			err = fmt.Errorf("GitHub REST transient status=%d", resp.StatusCode)
		}
		delay := retryDelay(attempt, time.Minute)
		v.logger.Warn(
			"Retrying GitHub REST verification in process",
			slog.String("path", path),
			slog.String("error", err.Error()),
			slog.Duration("backoff", delay),
		)
		if err := sleepContext(ctx, delay); err != nil {
			return err
		}
	}
}

func (v *githubVerifier) workflowFromRef(
	value string,
) (trustedWorkflow, string, bool) {
	base, ref, ok := strings.Cut(value, "@")
	if !ok {
		return trustedWorkflow{}, "", false
	}
	prefix := v.policy.Repository + "/"
	if !strings.HasPrefix(base, prefix) {
		return trustedWorkflow{}, "", false
	}
	path := strings.TrimPrefix(base, prefix)
	for _, workflow := range v.policy.TrustedWorkflows {
		if workflow.Path == path {
			return workflow, ref, true
		}
	}
	return trustedWorkflow{}, "", false
}

func (v *githubVerifier) Verify(
	ctx context.Context,
	job *scaleset.JobMessageBase,
) (verifiedJob, bool, string, error) {
	if job == nil || job.RunnerRequestID <= 0 || job.WorkflowRunID <= 0 {
		return verifiedJob{}, false, "scheduler identity incomplete", nil
	}
	if job.OwnerName+"/"+job.RepositoryName != v.policy.Repository {
		return verifiedJob{}, false, "repository mismatch", nil
	}
	if !containsString(job.RequestLabels, v.policy.ScaleSetName) {
		return verifiedJob{}, false, "runner-class label mismatch", nil
	}
	workflow, ref, ok := v.workflowFromRef(job.JobWorkflowRef)
	if !ok {
		return verifiedJob{}, false, "workflow path is not allowlisted", nil
	}
	if ref != "refs/heads/"+workflow.DefaultBranch {
		return verifiedJob{}, false, "workflow ref is not trusted default branch", nil
	}
	if !containsString(workflow.AllowedEvents, job.EventName) {
		return verifiedJob{}, false, "event is not allowed", nil
	}

	var run struct {
		ID         int64  `json:"id"`
		HeadSHA    string `json:"head_sha"`
		HeadBranch string `json:"head_branch"`
		Path       string `json:"path"`
		Event      string `json:"event"`
		Status     string `json:"status"`
		Actor      struct {
			Login string `json:"login"`
		} `json:"actor"`
		TriggeringActor struct {
			Login string `json:"login"`
		} `json:"triggering_actor"`
		Repository struct {
			FullName string `json:"full_name"`
		} `json:"repository"`
	}
	runPath := fmt.Sprintf(
		"/repos/%s/%s/actions/runs/%d",
		url.PathEscape(v.owner),
		url.PathEscape(v.repo),
		job.WorkflowRunID,
	)
	if err := v.getJSON(ctx, runPath, &run); err != nil {
		return verifiedJob{}, false, "", err
	}
	if run.Status == "completed" {
		return verifiedJob{}, false, "workflow run already terminal", nil
	}
	if run.ID != job.WorkflowRunID ||
		run.Repository.FullName != v.policy.Repository ||
		run.Path != workflow.Path ||
		run.Event != job.EventName ||
		run.HeadBranch != workflow.DefaultBranch ||
		len(run.HeadSHA) != 40 {
		return verifiedJob{}, false, "workflow run structured identity mismatch", nil
	}
	if !containsString(workflow.AllowedActorLogins, run.Actor.Login) {
		return verifiedJob{}, false, "actor is not allowed", nil
	}
	if !containsString(workflow.AllowedActorLogins, run.TriggeringActor.Login) {
		return verifiedJob{}, false, "triggering actor is not allowed", nil
	}

	var content struct {
		Type string `json:"type"`
		Path string `json:"path"`
		SHA  string `json:"sha"`
	}
	contentPath := fmt.Sprintf(
		"/repos/%s/%s/contents/%s?ref=%s",
		url.PathEscape(v.owner),
		url.PathEscape(v.repo),
		escapePath(workflow.Path),
		url.QueryEscape(run.HeadSHA),
	)
	if err := v.getJSON(ctx, contentPath, &content); err != nil {
		return verifiedJob{}, false, "", err
	}
	if content.Type != "file" ||
		content.Path != workflow.Path ||
		content.SHA != workflow.BlobSHA {
		return verifiedJob{}, false, "trusted workflow blob mismatch", nil
	}

	return verifiedJob{
		RunnerRequestID:      job.RunnerRequestID,
		WorkflowRunID:        job.WorkflowRunID,
		WorkflowPath:         workflow.Path,
		WorkflowBlobSHA:      content.SHA,
		ActorLogin:           run.Actor.Login,
		TriggeringActorLogin: run.TriggeringActor.Login,
		EventName:            run.Event,
	}, true, "", nil
}

func escapePath(path string) string {
	parts := strings.Split(path, "/")
	for i := range parts {
		parts[i] = url.PathEscape(parts[i])
	}
	return strings.Join(parts, "/")
}

type unixCapacityClient struct {
	socketPath string
	logger     *slog.Logger
}

func (c *unixCapacityClient) do(
	ctx context.Context,
	request map[string]any,
	expectedOperation string,
) (capacityResponse, error) {
	for attempt := 0; ; attempt++ {
		response, err := c.doOnce(ctx, request, expectedOperation)
		if err == nil {
			return response, nil
		}
		delay := retryDelay(attempt, time.Minute)
		c.logger.Warn(
			"Retrying v3 root capacity RPC in process",
			slog.String("operation", fmt.Sprint(request["operation"])),
			slog.String("error", err.Error()),
			slog.Duration("backoff", delay),
		)
		if err := sleepContext(ctx, delay); err != nil {
			return capacityResponse{}, err
		}
	}
}

func (c *unixCapacityClient) doOnce(
	ctx context.Context,
	request map[string]any,
	expectedOperation string,
) (capacityResponse, error) {
	dialer := net.Dialer{Timeout: 5 * time.Second}
	conn, err := dialer.DialContext(ctx, "unix", c.socketPath)
	if err != nil {
		return capacityResponse{}, err
	}
	defer conn.Close()
	unixConn, ok := conn.(*net.UnixConn)
	if !ok {
		return capacityResponse{}, fmt.Errorf("capacity connection is not Unix domain")
	}
	if err := json.NewEncoder(unixConn).Encode(request); err != nil {
		return capacityResponse{}, err
	}
	if err := unixConn.CloseWrite(); err != nil {
		return capacityResponse{}, err
	}
	var response capacityResponse
	if err := json.NewDecoder(unixConn).Decode(&response); err != nil {
		return capacityResponse{}, err
	}
	requestID, _ := request["request_id"].(string)
	if response.SchemaVersion != 3 ||
		response.Operation != expectedOperation ||
		response.RequestID != requestID ||
		response.Status == "" {
		return capacityResponse{}, fmt.Errorf("root response schema/identity mismatch")
	}
	return response, nil
}

func (c *unixCapacityClient) Reserve(
	ctx context.Context,
	requestID string,
	runnerName string,
) (capacityResponse, error) {
	return c.do(ctx, map[string]any{
		"schema_version": 3,
		"operation":      "RESERVE",
		"request_id":     requestID,
		"runner_name":    runnerName,
	}, "RESERVE_RESULT")
}

func (c *unixCapacityClient) Launch(
	ctx context.Context,
	requestID string,
	runnerName string,
	jitConfig string,
) (capacityResponse, error) {
	return c.do(ctx, map[string]any{
		"schema_version": 3,
		"operation":      "LAUNCH",
		"request_id":     requestID,
		"runner_name":    runnerName,
		"jit_config":     jitConfig,
	}, "LAUNCH_RESULT")
}

func (c *unixCapacityClient) Status(
	ctx context.Context,
	requestID string,
) (capacityResponse, error) {
	return c.do(ctx, map[string]any{
		"schema_version": 3,
		"operation":      "STATUS",
		"request_id":     requestID,
	}, "STATUS_RESULT")
}

func (c *unixCapacityClient) Cancel(
	ctx context.Context,
	requestID string,
) (capacityResponse, error) {
	return c.do(ctx, map[string]any{
		"schema_version": 3,
		"operation":      "CANCEL",
		"request_id":     requestID,
	}, "CANCEL_RESULT")
}

type retryingJITClient struct {
	inner  *scaleset.Client
	logger *slog.Logger
}

func (c *retryingJITClient) GenerateJitRunnerConfig(
	ctx context.Context,
	settings *scaleset.RunnerScaleSetJitRunnerSetting,
	scaleSetID int,
) (*scaleset.RunnerScaleSetJitRunnerConfig, error) {
	for attempt := 0; ; attempt++ {
		value, err := c.inner.GenerateJitRunnerConfig(ctx, settings, scaleSetID)
		if err == nil {
			return value, nil
		}
		delay := retryDelay(attempt, time.Minute)
		c.logger.Warn(
			"Retrying JIT generation in process",
			slog.String("error", err.Error()),
			slog.Duration("backoff", delay),
		)
		if err := sleepContext(ctx, delay); err != nil {
			return nil, err
		}
	}
}

func (c *retryingJITClient) RemoveRunner(ctx context.Context, runnerID int64) error {
	for attempt := 0; ; attempt++ {
		if err := c.inner.RemoveRunner(ctx, runnerID); err == nil {
			return nil
		} else {
			delay := retryDelay(attempt, time.Minute)
			c.logger.Warn(
				"Retrying orphan JIT removal in process",
				slog.Int64("runner_id", runnerID),
				slog.String("error", err.Error()),
				slog.Duration("backoff", delay),
			)
			if err := sleepContext(ctx, delay); err != nil {
				return err
			}
		}
	}
}

func runController(ctx context.Context, cfg runtimeConfig, logger *slog.Logger) error {
	policy, err := loadControllerPolicy(cfg.PolicyPath)
	if err != nil {
		return err
	}
	client, err := newScaleSetClient(cfg, policy)
	if err != nil {
		return err
	}
	scaleSet, err := requireScaleSet(ctx, client, policy)
	if err != nil {
		return err
	}
	client.SetSystemInfo(systemInfo(scaleSet.ID))

	hostname, err := os.Hostname()
	if err != nil || hostname == "" {
		hostname = "workspace-ci-v3-controller"
	}
	session, err := client.MessageSessionClient(ctx, scaleSet.ID, hostname)
	if err != nil {
		return fmt.Errorf("create v3 scale-set message session: %w", err)
	}
	defer session.Close(context.Background())

	retryingSession := &retryingSessionClient{
		inner:      session,
		logger:     logger.WithGroup("session"),
		maxBackoff: time.Minute,
	}
	l, err := listener.New(retryingSession, listener.Config{
		ScaleSetID: scaleSet.ID,
		MaxRunners: policy.MaxRunners,
		Logger:     logger.WithGroup("listener"),
	})
	if err != nil {
		return fmt.Errorf("create v3 listener: %w", err)
	}

	stateDir := filepath.Join(cfg.StateRoot, policy.RunnerClassID)
	ledger, err := newFileLedger(stateDir)
	if err != nil {
		return err
	}
	verifier, err := newGitHubVerifier(cfg, policy, logger.WithGroup("verify"))
	if err != nil {
		return err
	}
	root := &unixCapacityClient{
		socketPath: cfg.ProvisionerSock,
		logger:     logger.WithGroup("root"),
	}
	scaler := &v3Scaler{
		policy:     policy,
		verifier:   verifier,
		ledger:     ledger,
		session:    retryingSession,
		jit:        &retryingJITClient{inner: client, logger: logger.WithGroup("jit")},
		root:       root,
		scaleSetID: scaleSet.ID,
		logger:     logger.WithGroup("scaler"),
		now:        time.Now,
	}

	logger.Info(
		"Starting homogeneous Lambda CI v3 runner-class controller",
		slog.String("runner_class_id", policy.RunnerClassID),
		slog.String("repository", policy.Repository),
		slog.String("scale_set_name", policy.ScaleSetName),
		slog.Int("max_runners", policy.MaxRunners),
		slog.String("controller_policy_sha256", policy.ControllerPolicySHA256),
		slog.String("state_dir", stateDir),
	)
	if err := l.Run(ctx, scaler); err != nil && !errors.Is(err, context.Canceled) {
		return fmt.Errorf("v3 listener stopped: %w", err)
	}
	return nil
}

func main() {
	cfg, err := loadRuntimeConfig()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	logger := slog.New(slog.NewJSONHandler(os.Stderr, nil))
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer stop()
	if err := runController(ctx, cfg, logger); err != nil {
		logger.Error("v3 controller stopped", slog.String("error", err.Error()))
		os.Exit(1)
	}
}

// Keep strconv linked to this package for explicit config parsing diagnostics.
var _ = strconv.IntSize
