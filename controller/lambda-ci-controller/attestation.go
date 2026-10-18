package main

import (
	"context"
	"crypto/rsa"
	"errors"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/actions/scaleset"
	"github.com/golang-jwt/jwt/v5"
)

const (
	githubAPIVersion = "2022-11-28"
	controllerVerifiedAtLayout = "2006-01-02T15:04:05.000000Z07:00"
)

var (
	lowerHex40 = regexp.MustCompile(`^[0-9a-f]{40}$`)
	errTerminalWorkflowJob = errors.New("workflow job is already terminal")
)

type controllerAttestation struct {
	SchemaVersion                  int    `json:"schema_version"`
	Source                         string `json:"source"`
	Repository                     string `json:"repository"`
	ScaleSetName                   string `json:"scale_set_name"`
	JobMessageType                 string `json:"job_message_type"`
	RunnerRequestID                int64  `json:"runner_request_id"`
	WorkflowRunID                  int64  `json:"workflow_run_id"`
	JobID                          string `json:"job_id"`
	JobWorkflowRef                 string `json:"job_workflow_ref"`
	WorkflowPath                   string `json:"workflow_path"`
	WorkflowDefaultBranchCommitSHA string `json:"workflow_default_branch_commit_sha"`
	WorkflowBlobSHA                string `json:"workflow_blob_sha"`
	EventName                      string `json:"event_name"`
	JobDisplayName                 string `json:"job_display_name"`
	ActorLogin                     string `json:"actor_login"`
	TriggeringActorLogin           string `json:"triggering_actor_login"`
	PRNumber                       int    `json:"pr_number"`
	PRState                        string `json:"pr_state"`
	PRHeadRepository               string `json:"pr_head_repository"`
	CandidateSHA                   string `json:"candidate_sha"`
	CandidateVerification          string `json:"candidate_verification"`
	VerifiedAt                     string `json:"verified_at"`
}

type jobAttestor interface {
	Attest(
		context.Context,
		*scaleset.JobMessageBase,
		string,
		string,
	) (controllerAttestation, error)
}

type restTokenSource interface {
	Token(context.Context) (string, error)
}

type fixedTokenSource string

func (s fixedTokenSource) Token(context.Context) (string, error) {
	if strings.TrimSpace(string(s)) == "" {
		return "", fmt.Errorf("REST token is empty")
	}
	return string(s), nil
}

type appInstallationTokenSource struct {
	mu             sync.Mutex
	clientID       string
	installationID int64
	privateKey     *rsa.PrivateKey
	apiBase        string
	httpClient     *http.Client
	now            func() time.Time
	token          string
	expiresAt      time.Time
}

func newAppInstallationTokenSource(
	clientID string,
	installationID int64,
	privateKeyPEM string,
	apiBase string,
	httpClient *http.Client,
	now func() time.Time,
) (*appInstallationTokenSource, error) {
	key, err := jwt.ParseRSAPrivateKeyFromPEM([]byte(privateKeyPEM))
	if err != nil {
		return nil, fmt.Errorf("parse GitHub App private key: %w", err)
	}
	if strings.TrimSpace(clientID) == "" || installationID <= 0 {
		return nil, fmt.Errorf("GitHub App REST auth configuration is incomplete")
	}
	if httpClient == nil {
		httpClient = &http.Client{Timeout: 10 * time.Second}
	}
	if now == nil {
		now = time.Now
	}
	return &appInstallationTokenSource{
		clientID:       clientID,
		installationID: installationID,
		privateKey:     key,
		apiBase:        strings.TrimRight(apiBase, "/"),
		httpClient:     httpClient,
		now:            now,
	}, nil
}

func (s *appInstallationTokenSource) Token(ctx context.Context) (string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	now := s.now().UTC()
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
		return "", fmt.Errorf("create GitHub App access-token request: %w", err)
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("Authorization", "Bearer "+appJWT)
	req.Header.Set("X-GitHub-Api-Version", githubAPIVersion)

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("request GitHub App installation token: %w", err)
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
		return "", fmt.Errorf("decode GitHub App installation token: %w", err)
	}
	if strings.TrimSpace(payload.Token) == "" || payload.ExpiresAt.IsZero() {
		return "", fmt.Errorf("GitHub App installation token response is incomplete")
	}
	s.token = payload.Token
	s.expiresAt = payload.ExpiresAt.UTC()
	return s.token, nil
}

type githubJobAttestor struct {
	owner      string
	repo       string
	apiBase    string
	httpClient *http.Client
	tokenSource restTokenSource
	now        func() time.Time
}

func parseRepositoryURL(raw string) (string, string, error) {
	u, err := url.Parse(raw)
	if err != nil {
		return "", "", fmt.Errorf("parse GitHub repository URL: %w", err)
	}
	if u.Scheme != "https" || !strings.EqualFold(u.Hostname(), "github.com") {
		return "", "", fmt.Errorf("admission v2 currently requires https://github.com")
	}
	parts := strings.Split(strings.Trim(u.Path, "/"), "/")
	if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
		return "", "", fmt.Errorf("GitHub repository URL must be owner/repository")
	}
	return parts[0], parts[1], nil
}

func newGitHubJobAttestor(cfg config) (*githubJobAttestor, error) {
	owner, repo, err := parseRepositoryURL(cfg.GitHubURL)
	if err != nil {
		return nil, err
	}
	httpClient := &http.Client{Timeout: 10 * time.Second}
	const apiBase = "https://api.github.com"

	var source restTokenSource
	if cfg.AppClientID != "" {
		privateKey, err := readSecretFile(cfg.AppPrivateKey)
		if err != nil {
			return nil, fmt.Errorf("read GitHub App private key for attestor: %w", err)
		}
		source, err = newAppInstallationTokenSource(
			cfg.AppClientID,
			cfg.AppInstallID,
			privateKey,
			apiBase,
			httpClient,
			time.Now,
		)
		if err != nil {
			return nil, err
		}
	} else {
		token, err := readSecretFile(cfg.PATFile)
		if err != nil {
			return nil, fmt.Errorf("read controller PAT for attestor: %w", err)
		}
		source = fixedTokenSource(token)
	}

	return &githubJobAttestor{
		owner:       owner,
		repo:        repo,
		apiBase:     apiBase,
		httpClient:  httpClient,
		tokenSource: source,
		now:         time.Now,
	}, nil
}

func (a *githubJobAttestor) getJSON(
	ctx context.Context,
	path string,
	target any,
) error {
	token, err := a.tokenSource.Token(ctx)
	if err != nil {
		return err
	}
	endpoint := strings.TrimRight(a.apiBase, "/") + path
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return fmt.Errorf("create GitHub REST request: %w", err)
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("X-GitHub-Api-Version", githubAPIVersion)
	resp, err := a.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("GitHub REST request failed: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return fmt.Errorf(
			"GitHub REST status=%d path=%s body=%q",
			resp.StatusCode,
			path,
			strings.TrimSpace(string(body)),
		)
	}
	if err := json.NewDecoder(resp.Body).Decode(target); err != nil {
		return fmt.Errorf("decode GitHub REST response %s: %w", path, err)
	}
	return nil
}

func requestCommandForWorkload(workload string) (string, error) {
	switch workload {
	case defaultProfile:
		return "/lambda-ci-p5", nil
	case gpuProfile:
		return "/lambda-ci-p5-gpu", nil
	case modelEvalWorkload:
		return "/lambda-ci-qwen35-pilot", nil
	case dualModelEvalWorkload:
		return "/lambda-ci-qwen35-dual-pilot", nil
	default:
		return "", fmt.Errorf("admission v2 workload command rejected: %s", workload)
	}
}

func parseAdmissionDisplayClaim(
	displayName string,
	workload string,
	command string,
) (int, string, error) {
	pattern := regexp.MustCompile(
		`^wc-admission-v1\|workload=` + regexp.QuoteMeta(workload) +
			`\|pr=([1-9][0-9]*)\|request=` + regexp.QuoteMeta(command) +
			` ([0-9a-f]{40})$`,
	)
	match := pattern.FindStringSubmatch(displayName)
	if match == nil {
		return 0, "", fmt.Errorf("job display claim does not match admission grammar")
	}
	prNumber, err := strconv.Atoi(match[1])
	if err != nil || prNumber <= 0 {
		return 0, "", fmt.Errorf("job display claim PR number is invalid")
	}
	return prNumber, match[2], nil
}

func trustedWorkflowPath(
	jobWorkflowRef string,
	owner string,
	repo string,
) (string, error) {
	base, ref, ok := strings.Cut(jobWorkflowRef, "@")
	if !ok || ref != "refs/heads/main" {
		return "", fmt.Errorf("job workflow ref is not the trusted default branch")
	}
	prefix := owner + "/" + repo + "/"
	if !strings.HasPrefix(base, prefix) {
		return "", fmt.Errorf("job workflow ref repository mismatch")
	}
	path := strings.TrimPrefix(base, prefix)
	if !strings.HasPrefix(path, ".github/workflows/") ||
		strings.Contains(path, "..") ||
		!(strings.HasSuffix(path, ".yml") || strings.HasSuffix(path, ".yaml")) {
		return "", fmt.Errorf("job workflow path is invalid")
	}
	return path, nil
}

func escapeContentPath(path string) string {
	parts := strings.Split(path, "/")
	for i := range parts {
		parts[i] = url.PathEscape(parts[i])
	}
	return strings.Join(parts, "/")
}

func (a *githubJobAttestor) Attest(
	ctx context.Context,
	job *scaleset.JobMessageBase,
	scaleSetName string,
	workload string,
) (controllerAttestation, error) {
	if job == nil {
		return controllerAttestation{}, fmt.Errorf("job metadata is required")
	}
	if job.OwnerName != a.owner || job.RepositoryName != a.repo {
		return controllerAttestation{}, fmt.Errorf("job repository mismatch")
	}
	if job.EventName != "issue_comment" {
		return controllerAttestation{}, fmt.Errorf("job event is not issue_comment")
	}
	if job.WorkflowRunID <= 0 {
		return controllerAttestation{}, fmt.Errorf("workflow run identity is incomplete")
	}
	messageType := string(job.MessageType)
	switch job.MessageType {
	case scaleset.MessageTypeJobAvailable:
		if job.RunnerRequestID <= 0 {
			return controllerAttestation{}, fmt.Errorf("JobAvailable runner request identity is incomplete")
		}
	case scaleset.MessageTypeJobAssigned:
		// GitHub may omit runnerRequestId from JobAssigned lifecycle/recovery
		// messages. The canonical workflow-job identity is resolved below
		// through the read-only Actions REST API instead of inventing an ID.
	default:
		return controllerAttestation{}, fmt.Errorf("unsupported job message type %q", messageType)
	}

	command, err := requestCommandForWorkload(workload)
	if err != nil {
		return controllerAttestation{}, err
	}
	prNumber, candidateSHA, err := parseAdmissionDisplayClaim(
		job.JobDisplayName,
		workload,
		command,
	)
	if err != nil {
		return controllerAttestation{}, err
	}
	workflowPath, err := trustedWorkflowPath(job.JobWorkflowRef, a.owner, a.repo)
	if err != nil {
		return controllerAttestation{}, err
	}

	var run struct {
		ID         int64  `json:"id"`
		HeadSHA    string `json:"head_sha"`
		Path       string `json:"path"`
		Event      string `json:"event"`
		Status     string `json:"status"`
		Conclusion string `json:"conclusion"`
		Actor      struct{ Login string `json:"login"` } `json:"actor"`
		Triggering struct{ Login string `json:"login"` } `json:"triggering_actor"`
		Repository struct{ FullName string `json:"full_name"` } `json:"repository"`
	}
	runPath := fmt.Sprintf(
		"/repos/%s/%s/actions/runs/%d",
		url.PathEscape(a.owner),
		url.PathEscape(a.repo),
		job.WorkflowRunID,
	)
	if err := a.getJSON(ctx, runPath, &run); err != nil {
		return controllerAttestation{}, err
	}
	if run.Status == "completed" {
		return controllerAttestation{}, fmt.Errorf(
			"%w: workflow run %d completed with conclusion %q",
			errTerminalWorkflowJob,
			run.ID,
			run.Conclusion,
		)
	}
	if run.ID != job.WorkflowRunID ||
		run.Path != workflowPath ||
		run.Event != job.EventName ||
		run.Repository.FullName != a.owner+"/"+a.repo ||
		!lowerHex40.MatchString(run.HeadSHA) ||
		run.Actor.Login == "" ||
		run.Triggering.Login == "" {
		return controllerAttestation{}, fmt.Errorf("workflow run attestation mismatch")
	}

	var jobs struct {
		TotalCount int `json:"total_count"`
		Jobs       []struct {
			ID         int64  `json:"id"`
			RunID      int64  `json:"run_id"`
			Name       string `json:"name"`
			Status     string `json:"status"`
			Conclusion string `json:"conclusion"`
		} `json:"jobs"`
	}
	jobsPath := fmt.Sprintf(
		"/repos/%s/%s/actions/runs/%d/jobs?per_page=100",
		url.PathEscape(a.owner),
		url.PathEscape(a.repo),
		job.WorkflowRunID,
	)
	if err := a.getJSON(ctx, jobsPath, &jobs); err != nil {
		return controllerAttestation{}, err
	}
	var canonicalJobID int64
	matches := 0
	for _, runJob := range jobs.Jobs {
		if runJob.Name == job.JobDisplayName {
			if runJob.ID <= 0 || (runJob.RunID != 0 && runJob.RunID != job.WorkflowRunID) {
				return controllerAttestation{}, fmt.Errorf("workflow job REST identity is invalid")
			}
			if runJob.Status == "completed" {
				return controllerAttestation{}, fmt.Errorf(
					"%w: workflow job %d completed with conclusion %q",
					errTerminalWorkflowJob,
					runJob.ID,
					runJob.Conclusion,
				)
			}
			canonicalJobID = runJob.ID
			matches++
		}
	}
	if matches != 1 {
		return controllerAttestation{}, fmt.Errorf(
			"workflow job display claim matched %d REST jobs; require exactly one",
			matches,
		)
	}

	var content struct {
		Type string `json:"type"`
		Path string `json:"path"`
		SHA  string `json:"sha"`
	}
	contentPath := fmt.Sprintf(
		"/repos/%s/%s/contents/%s?ref=%s",
		url.PathEscape(a.owner),
		url.PathEscape(a.repo),
		escapeContentPath(workflowPath),
		url.QueryEscape(run.HeadSHA),
	)
	if err := a.getJSON(ctx, contentPath, &content); err != nil {
		return controllerAttestation{}, err
	}
	if content.Type != "file" ||
		content.Path != workflowPath ||
		!lowerHex40.MatchString(content.SHA) {
		return controllerAttestation{}, fmt.Errorf("workflow blob attestation mismatch")
	}

	var pull struct {
		Number int    `json:"number"`
		State  string `json:"state"`
		Head    struct {
			SHA  string `json:"sha"`
			Repo struct {
				FullName string `json:"full_name"`
			} `json:"repo"`
		} `json:"head"`
	}
	pullPath := fmt.Sprintf(
		"/repos/%s/%s/pulls/%d",
		url.PathEscape(a.owner),
		url.PathEscape(a.repo),
		prNumber,
	)
	if err := a.getJSON(ctx, pullPath, &pull); err != nil {
		return controllerAttestation{}, err
	}
	if pull.Number != prNumber ||
		pull.State != "open" ||
		pull.Head.Repo.FullName != a.owner+"/"+a.repo ||
		pull.Head.SHA != candidateSHA ||
		!lowerHex40.MatchString(pull.Head.SHA) {
		return controllerAttestation{}, fmt.Errorf("PR head attestation mismatch")
	}

	return controllerAttestation{
		SchemaVersion:                  2,
		Source:                         "github_scale_set_controller",
		Repository:                     a.owner + "/" + a.repo,
		ScaleSetName:                   scaleSetName,
		JobMessageType:                 messageType,
		RunnerRequestID:                job.RunnerRequestID,
		WorkflowRunID:                  job.WorkflowRunID,
		JobID:                          strconv.FormatInt(canonicalJobID, 10),
		JobWorkflowRef:                 job.JobWorkflowRef,
		WorkflowPath:                   workflowPath,
		WorkflowDefaultBranchCommitSHA: run.HeadSHA,
		WorkflowBlobSHA:                content.SHA,
		EventName:                      job.EventName,
		JobDisplayName:                 job.JobDisplayName,
		ActorLogin:                     run.Actor.Login,
		TriggeringActorLogin:           run.Triggering.Login,
		PRNumber:                       prNumber,
		PRState:                        pull.State,
		PRHeadRepository:               pull.Head.Repo.FullName,
		CandidateSHA:                   candidateSHA,
		CandidateVerification:          "PR_HEAD_MATCH",
		VerifiedAt:                     a.now().UTC().Format(controllerVerifiedAtLayout),
	}, nil
}

func deterministicAdmissionExecutionIDs(
	workload string,
	att controllerAttestation,
) (string, string, error) {
	var prefix string
	switch workload {
	case defaultProfile:
		prefix = "lambda-research-engine-"
	case gpuProfile, modelEvalWorkload, dualModelEvalWorkload:
		prefix = "lambda-research-engine-gpu-"
	default:
		return "", "", fmt.Errorf("deterministic runner workload rejected: %s", workload)
	}
	material := fmt.Sprintf(
		"%s|%s|%s|%d|%s|%s|%s",
		att.Repository,
		att.ScaleSetName,
		workload,
		att.WorkflowRunID,
		att.JobID,
		att.JobDisplayName,
		att.CandidateSHA,
	)
	sum := sha256.Sum256([]byte(material))

	raw := append([]byte(nil), sum[:16]...)
	raw[6] = (raw[6] & 0x0f) | 0x50
	raw[8] = (raw[8] & 0x3f) | 0x80
	h := hex.EncodeToString(raw)
	requestID := fmt.Sprintf(
		"%s-%s-%s-%s-%s",
		h[0:8],
		h[8:12],
		h[12:16],
		h[16:20],
		h[20:32],
	)
	runnerName := prefix + hex.EncodeToString(sum[16:22])
	return requestID, runnerName, nil
}
