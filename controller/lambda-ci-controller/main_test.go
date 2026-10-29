package main

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"net"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/actions/scaleset"
)

type fakeRunnerJITClient struct {
	runner        *scaleset.RunnerReference
	removedIDs    []int64
	generated     int
}

func (f *fakeRunnerJITClient) GenerateJitRunnerConfig(
	context.Context,
	*scaleset.RunnerScaleSetJitRunnerSetting,
	int,
) (*scaleset.RunnerScaleSetJitRunnerConfig, error) {
	f.generated++
	return &scaleset.RunnerScaleSetJitRunnerConfig{
		Runner: &scaleset.RunnerReference{ID: 9001, Name: "generated", RunnerScaleSetID: 1},
		EncodedJITConfig: "opaque",
	}, nil
}

func (f *fakeRunnerJITClient) GetRunnerByName(
	context.Context,
	string,
) (*scaleset.RunnerReference, error) {
	return f.runner, nil
}

func (f *fakeRunnerJITClient) RemoveRunner(_ context.Context, id int64) error {
	f.removedIDs = append(f.removedIDs, id)
	f.runner = nil
	return nil
}

func TestProvisionRequestSchemaIsExact(t *testing.T) {
	req := provisionRequest{
		SchemaVersion: 1,
		RequestID:     "01234567-89ab-4cde-8fab-0123456789ab",
		ProjectID:     "research-engine",
		Profile:       "cpu-test",
		RunnerName:    "lambda-research-engine-test",
		JITConfig:     "opaque-secret",
	}
	raw, err := json.Marshal(req)
	if err != nil {
		t.Fatal(err)
	}
	var got map[string]any
	if err := json.Unmarshal(raw, &got); err != nil {
		t.Fatal(err)
	}
	want := []string{"jit_config", "profile", "project_id", "request_id", "runner_name", "schema_version"}
	gotKeys := make([]string, 0, len(got))
	for _, key := range want {
		if _, ok := got[key]; ok {
			gotKeys = append(gotKeys, key)
		}
	}
	if !reflect.DeepEqual(gotKeys, want) || len(got) != len(want) {
		t.Fatalf("unexpected request schema: %#v", got)
	}
}

func TestReadSecretFileRejectsBroadPermissions(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "token")
	if err := os.WriteFile(path, []byte("secret\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := readSecretFile(path); err == nil {
		t.Fatal("broad credential permissions accepted")
	}
	if err := os.Chmod(path, 0o600); err != nil {
		t.Fatal(err)
	}
	value, err := readSecretFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if value != "secret" {
		t.Fatalf("unexpected secret value %q", value)
	}
}

func TestProvisionerSocketReceivesJITButResponseDoesNotEchoIt(t *testing.T) {
	dir := t.TempDir()
	socketPath := filepath.Join(dir, "provisioner.sock")
	ln, err := net.Listen("unix", socketPath)
	if err != nil {
		t.Fatal(err)
	}
	defer ln.Close()

	secret := "encoded-jit-secret"
	received := make(chan provisionRequest, 1)
	go func() {
		conn, err := ln.Accept()
		if err != nil {
			return
		}
		defer conn.Close()
		var req provisionRequest
		if err := json.NewDecoder(bufio.NewReader(conn)).Decode(&req); err != nil {
			return
		}
		received <- req
		_ = json.NewEncoder(conn).Encode(provisionResponse{
			SchemaVersion: 1,
			Status:        "ACCEPTED",
			RequestID:     req.RequestID,
		})
	}()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	response, err := sendProvisionRequest(ctx, socketPath, provisionRequest{
		SchemaVersion: 1,
		RequestID:     "01234567-89ab-4cde-8fab-0123456789ab",
		ProjectID:     "research-engine",
		Profile:       "cpu-test",
		RunnerName:    "lambda-research-engine-test",
		JITConfig:     secret,
	})
	if err != nil {
		t.Fatal(err)
	}
	if response.Status != "ACCEPTED" {
		t.Fatalf("unexpected status %s", response.Status)
	}
	req := <-received
	if req.JITConfig != secret {
		t.Fatal("JIT config was not delivered to provisioner")
	}
	encoded, _ := json.Marshal(response)
	if string(encoded) == secret || contains(string(encoded), secret) {
		t.Fatal("provisioner response echoed JIT secret")
	}
}

func TestControllerIdentityIsDerivedFromProjectAndLane(t *testing.T) {
	cases := []struct { project, lane, scaleSet, prefix, profile string }{
		{"research-engine","cpu","lambda-research-engine","lambda-research-engine-","cpu-test"},
		{"research-engine","gpu","lambda-research-engine-gpu","lambda-research-engine-gpu-","gpu-small"},
		{"padataset","cpu","lambda-padataset","lambda-padataset-","cpu-test"},
		{"padataset","gpu","lambda-padataset-gpu","lambda-padataset-gpu-","gpu-small"},
		{"future-research","gpu","lambda-future-research-gpu","lambda-future-research-gpu-","gpu-small"},
	}
	for _, tc := range cases {
		scale,prefix,profile,err := derivedControllerIdentity(tc.project,tc.lane)
		if err != nil || scale != tc.scaleSet || prefix != tc.prefix || profile != tc.profile {
			t.Fatalf("identity drift %#v scale=%q prefix=%q profile=%q err=%v",tc,scale,prefix,profile,err)
		}
	}
	for _, bad := range []struct{project,lane string}{{"ResearchEngine","cpu"},{"x","cpu"},{"research_engine","cpu"},{"research-engine","heavy"}} {
		if _,_,_,err := derivedControllerIdentity(bad.project,bad.lane); err == nil { t.Fatalf("invalid accepted %#v",bad) }
	}
}

func TestWorkloadSelectionIsGenericStrictRouteParsing(t *testing.T) {
	for _, route := range []string{"cpu-test","gpu-small","model-eval-local-extract-wave1","padataset-rf-benchmark-7"} {
		claim := "wc-admission-v1|workload="+route+"|pr=101|request=/lambda-ci-example "+strings.Repeat("a",40)
		got,err := workloadForDisplayClaim(claim)
		if err != nil || got != route { t.Fatalf("route parse failed %q got=%q err=%v",route,got,err) }
	}
	for _, invalid := range []string{
		"wc-admission-v1|workload=BAD|pr=101|request=/lambda-ci-example "+strings.Repeat("a",40),
		"wc-admission-v1|workload=../../root|pr=101|request=/lambda-ci-example "+strings.Repeat("a",40),
		"not-an-admission-claim",
	} {
		if _,err := workloadForDisplayClaim(invalid); err == nil { t.Fatalf("invalid claim accepted %q",invalid) }
	}
}

func TestRunnerNamesUseConfiguredDerivedPrefix(t *testing.T) {
	for _, prefix := range []string{"lambda-research-engine-","lambda-research-engine-gpu-","lambda-padataset-","lambda-padataset-gpu-"} {
		name,err := runnerName(prefix)
		if err != nil || !strings.HasPrefix(name,prefix) { t.Fatalf("runner prefix failed %q name=%q err=%v",prefix,name,err) }
	}
	if _,err := runnerName("arbitrary"); err == nil { t.Fatal("invalid runner prefix accepted") }
}

func contains(haystack, needle string) bool {
	if len(needle) == 0 {
		return true
	}
	for i := 0; i+len(needle) <= len(haystack); i++ {
		if haystack[i:i+len(needle)] == needle {
			return true
		}
	}
	return false
}


func setGenericControllerEnv(t *testing.T, projectID, lane string) {
	scale,prefix,_,err := derivedControllerIdentity(projectID,lane)
	if err != nil { t.Fatal(err) }
	t.Setenv("WORKSPACE_CI_GITHUB_URL","https://github.com/adamtrott78/"+projectID)
	t.Setenv("WORKSPACE_CI_SCALESET_NAME",scale)
	t.Setenv("WORKSPACE_CI_PROJECT_ID",projectID)
	t.Setenv("WORKSPACE_CI_LANE",lane)
	t.Setenv("WORKSPACE_CI_RUNNER_PREFIX",prefix)
	t.Setenv("WORKSPACE_CI_PROVISIONER_SOCKET","")
	t.Setenv("WORKSPACE_CI_APP_CLIENT_ID","")
	t.Setenv("WORKSPACE_CI_APP_INSTALLATION_ID","")
	t.Setenv("WORKSPACE_CI_APP_PRIVATE_KEY_FILE","")
	t.Setenv("WORKSPACE_CI_PAT_FILE","/tmp/controller-token-for-config-test")
}

func TestAdmissionV2RequiresExplicitYesAndGenericProjectConfig(t *testing.T) {
	setGenericControllerEnv(t,"padataset","gpu")
	t.Setenv("WORKSPACE_CI_ADMISSION_V2_ENABLED","")
	cfg,err := loadConfig()
	if err != nil { t.Fatal(err) }
	if cfg.AdmissionV2 || cfg.ProjectID!="padataset" || cfg.Lane!="gpu" || cfg.ScaleSetName!="lambda-padataset-gpu" || cfg.RunnerPrefix!="lambda-padataset-gpu-" || cfg.Profile!="gpu-small" {
		t.Fatalf("generic config drift %#v",cfg)
	}
	t.Setenv("WORKSPACE_CI_ADMISSION_V2_ENABLED","YES")
	cfg,err=loadConfig()
	if err != nil || !cfg.AdmissionV2 { t.Fatalf("v2 YES failed %#v err=%v",cfg,err) }
	t.Setenv("WORKSPACE_CI_SCALESET_NAME","lambda-research-engine-gpu")
	if _,err:=loadConfig(); err==nil { t.Fatal("cross-project scale-set accepted") }
}

func TestControllerRequiresExplicitProjectIdentity(t *testing.T) {
	setGenericControllerEnv(t,"research-engine","cpu")
	t.Setenv("WORKSPACE_CI_PROJECT_ID","")
	if _,err:=loadConfig(); err==nil { t.Fatal("missing project id accepted") }
}

func TestAdmissionV2CanProvisionFromPreAttestedJobAvailable(t *testing.T) {
	stats := &scaleset.RunnerScaleSetStatistic{
		TotalAvailableJobs: 1,
		TotalAcquiredJobs:  0,
		TotalAssignedJobs:  0,
	}
	if got := desiredRunnerTarget(stats, 1, 0, true); got != 1 {
		t.Fatalf("pre-attested JobAvailable did not create runner target: %d", got)
	}
	if got := desiredRunnerTarget(stats, 0, 0, true); got != 0 {
		t.Fatalf("unattested available job unexpectedly created runner target: %d", got)
	}
}

func TestAdmissionV2TargetRemainsBounded(t *testing.T) {
	stats := &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 99}
	if got := desiredRunnerTarget(stats, 99, 0, true); got != maxRunners {
		t.Fatalf("target exceeded maxRunners: %d", got)
	}
}

func TestAdmissionV2AssignedStatisticAloneNeverCreatesExecutionTarget(t *testing.T) {
	stats := &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1}
	if got := desiredRunnerTarget(stats, 0, 0, true); got != 0 {
		t.Fatalf("aggregate assigned statistic became execution authority: %d", got)
	}
	if got := desiredRunnerTarget(stats, 0, 0, false); got != 1 {
		t.Fatalf("legacy non-v2 target semantics unexpectedly changed: %d", got)
	}
}

type neverCalledAttestor struct {
	calls int
}

func (a *neverCalledAttestor) Attest(
	context.Context,
	*scaleset.JobMessageBase,
	string,
	string,
) (controllerAttestation, error) {
	a.calls++
	return controllerAttestation{}, nil
}

type rejectingAdmissionAttestor struct {
	calls int
}

func (a *rejectingAdmissionAttestor) Attest(
	context.Context,
	*scaleset.JobMessageBase,
	string,
	string,
) (controllerAttestation, error) {
	a.calls++
	return controllerAttestation{}, fmt.Errorf("synthetic admission rejection")
}

type staticAdmissionAttestor struct {
	calls int
}

func (a *staticAdmissionAttestor) Attest(
	_ context.Context,
	job *scaleset.JobMessageBase,
	scaleSetName string,
	workload string,
) (controllerAttestation, error) {
	a.calls++
	return controllerAttestation{
		SchemaVersion:    2,
		Source:           "test",
		Repository:       "adamtrott78/research-engine",
		ScaleSetName:     scaleSetName,
		JobMessageType:   string(job.MessageType),
		RunnerRequestID:  job.RunnerRequestID,
		WorkflowRunID:    job.WorkflowRunID,
		JobID:            "777",
		JobDisplayName:   job.JobDisplayName,
		CandidateSHA:     testCandidateSHA,
	}, nil
}

func TestAvailableAdmissionIsStagedBeforeAggregateDivergenceDecision(t *testing.T) {
	dir := t.TempDir()
	attestor := &staticAdmissionAttestor{}
	s := &scaler{
		active:       make(map[string]string),
		scaleSetID:   17,
		projectID:    "research-engine",
		lane:         "cpu",
		scaleSetName: "lambda-research-engine",
		runnerPrefix: "lambda-research-engine-",
		stateDir:     dir,
		admissionV2:  true,
		attestor:     attestor,
		pending:      make(map[string]pendingAdmissionJob),
		logger:       slog.Default(),
	}

	available := availableCPUJob()
	requestIDs, stagedKeys, err := s.stageAvailableAdmissions(
		context.Background(),
		[]*scaleset.JobAvailable{available},
	)
	if err != nil {
		t.Fatal(err)
	}
	if attestor.calls != 1 {
		t.Fatalf("available claim was not independently attested: %d", attestor.calls)
	}
	if !reflect.DeepEqual(requestIDs, []int64{available.RunnerRequestID}) {
		t.Fatalf("unexpected request ids: %#v", requestIDs)
	}
	if !reflect.DeepEqual(stagedKeys, []string{"777"}) {
		t.Fatalf("unexpected staged keys: %#v", stagedKeys)
	}
	if got := reconstructableAssignedCount(len(s.active), len(s.pending)); got != 1 {
		t.Fatalf("attested available claim was not reconstructable before divergence check: %d", got)
	}
	stats := &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1}
	if stats.TotalAssignedJobs > reconstructableAssignedCount(len(s.active), len(s.pending)) {
		t.Fatal("normal aggregate/lifecycle skew would still be classified as divergence")
	}
	if _, err := os.Stat(filepath.Join(dir, "quarantine.json")); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("staging authoritative available work unexpectedly created quarantine: %v", err)
	}
}

func TestNewQuarantineInvalidatesOlderReadyRetryGate(t *testing.T) {
	dir := t.TempDir()
	s := &scaler{
		active:       make(map[string]string),
		scaleSetID:   88,
		projectID:    "research-engine",
		lane:         "gpu",
		scaleSetName: "lambda-research-engine-gpu",
		stateDir:     dir,
		pending:      make(map[string]pendingAdmissionJob),
		logger:       slog.Default(),
	}
	ready := map[string]any{
		"schema_version": 1,
		"status": "READY_FOR_SINGLE_RETRY",
		"receipt_id": "11111111-2222-4333-8444-555555555555",
		"project_id": "research-engine",
		"lane": "gpu",
		"scale_set_name": "lambda-research-engine-gpu",
		"old_scale_set_id": 77,
		"new_scale_set_id": 88,
		"reset_generation": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
		"automatic_workflow_triggered": false,
	}
	if err := atomicWriteJSON(s.readyForSingleRetryPath(), ready); err != nil {
		t.Fatal(err)
	}
	stats := &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1}
	if err := s.persistAssignmentQuarantine(stats, 0, 0); err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(s.readyForSingleRetryPath())
	if err != nil {
		t.Fatal(err)
	}
	var got map[string]any
	if err := json.Unmarshal(raw, &got); err != nil {
		t.Fatal(err)
	}
	if got["status"] != "RECOVERY_RETRY_INVALIDATED" ||
		got["previous_status"] != "READY_FOR_SINGLE_RETRY" {
		t.Fatalf("older retry gate remained consumable: %#v", got)
	}
	if got["invalidated_by_quarantine_receipt_id"] != s.quarantineID {
		t.Fatalf("retry invalidation was not bound to new quarantine: %#v", got)
	}
	if _, err := os.Stat(s.quarantinePath()); err != nil {
		t.Fatalf("new quarantine was not durably persisted: %v", err)
	}
}

func TestAssignmentDivergenceQuarantinesAndSuppressesNewAcquisition(t *testing.T) {
	dir := t.TempDir()
	client := &fakeRunnerJITClient{}
	attestor := &neverCalledAttestor{}
	s := &scaler{
		active:       make(map[string]string),
		client:       client,
		scaleSetID:   17,
		projectID:    "workspace-control",
		lane:         "cpu",
		scaleSetName: "lambda-workspace-control",
		runnerPrefix: "lambda-workspace-control-",
		stateDir:     dir,
		admissionV2:  true,
		attestor:     attestor,
		pending:      make(map[string]pendingAdmissionJob),
		logger:       slog.Default(),
	}

	if err := s.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics: &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1},
	}); err != nil {
		t.Fatal(err)
	}
	if s.quarantined {
		t.Fatalf("aggregate-only startup skew falsely quarantined lane: %#v", s)
	}
	if _, err := os.Stat(filepath.Join(dir, "quarantine.json")); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("aggregate-only skew created durable quarantine: %v", err)
	}

	incomplete := assignedCPUJob()
	incomplete.JobWorkflowRef = ""
	if err := s.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics:          &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1},
		JobAssignedMessages: []*scaleset.JobAssigned{incomplete},
	}); err != nil {
		t.Fatal(err)
	}
	if !s.quarantined || s.quarantineID == "" {
		t.Fatalf("unreconstructable lifecycle evidence did not quarantine lane: %#v", s)
	}
	if _, err := os.Stat(filepath.Join(dir, "quarantine.json")); err != nil {
		t.Fatalf("durable quarantine receipt missing: %v", err)
	}

	available := availableCPUJob()
	if err := s.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics:         &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 0},
		JobAvailableMessages: []*scaleset.JobAvailable{available},
	}); err != nil {
		t.Fatal(err)
	}
	if attestor.calls != 0 {
		t.Fatalf("quarantined lane attested new available work: %d calls", attestor.calls)
	}
	if client.generated != 0 {
		t.Fatalf("quarantined lane generated JIT configuration: %d", client.generated)
	}
	if !s.quarantined {
		t.Fatal("aggregate zero improperly auto-cleared quarantine")
	}
}

func TestAssignedAttestationRejectionQuarantinesWithoutCrashingController(t *testing.T) {
	dir := t.TempDir()
	attestor := &rejectingAdmissionAttestor{}
	s := &scaler{
		active:       make(map[string]string),
		scaleSetID:   17,
		projectID:    "research-engine",
		lane:         "gpu",
		scaleSetName: "lambda-research-engine-gpu",
		runnerPrefix: "lambda-research-engine-gpu-",
		stateDir:     dir,
		admissionV2:  true,
		attestor:     attestor,
		pending:      make(map[string]pendingAdmissionJob),
		logger:       slog.Default(),
	}
	assigned := assignedCPUJob()
	if err := s.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics:          &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1},
		JobAssignedMessages: []*scaleset.JobAssigned{assigned},
	}); err != nil {
		t.Fatalf("admission rejection escaped as controller-fatal error: %v", err)
	}
	if attestor.calls != 1 {
		t.Fatalf("assigned recovery metadata was not attested: %d", attestor.calls)
	}
	if !s.quarantined {
		t.Fatal("rejected assigned metadata did not fail lane closed")
	}
	if _, err := os.Stat(s.quarantinePath()); err != nil {
		t.Fatalf("rejected assigned metadata did not persist quarantine: %v", err)
	}
}

func TestControllerQuarantineSurvivesRestart(t *testing.T) {
	dir := t.TempDir()
	receipt := laneQuarantineReceipt{
		SchemaVersion:       1,
		ReceiptID:           "01234567-89ab-4cde-8fab-0123456789ab",
		Status:              "ASSIGNMENT_DIVERGENCE_QUARANTINED",
		ProjectID:           "workspace-control",
		Lane:                "cpu",
		ScaleSetName:        "lambda-workspace-control",
		ScaleSetID:          31,
		TotalAssignedJobs:   1,
		ReconstructableJobs: 0,
		ObservedAt:          time.Now().UTC().Format(time.RFC3339Nano),
	}
	if err := atomicWriteJSON(filepath.Join(dir, "quarantine.json"), receipt); err != nil {
		t.Fatal(err)
	}
	s := &scaler{
		scaleSetID:   31,
		projectID:    "workspace-control",
		lane:         "cpu",
		scaleSetName: "lambda-workspace-control",
		stateDir:     dir,
	}
	if err := s.loadQuarantine(); err != nil {
		t.Fatal(err)
	}
	if !s.quarantined || s.quarantineID != receipt.ReceiptID {
		t.Fatalf("quarantine did not survive restart: %#v", s)
	}
}

func TestQuarantineAutoResolutionRequiresCompleteReconstructedAssignment(t *testing.T) {
	dir := t.TempDir()
	s := &scaler{
		active:       make(map[string]string),
		scaleSetID:   41,
		projectID:    "workspace-control",
		lane:         "cpu",
		scaleSetName: "lambda-workspace-control",
		stateDir:     dir,
		pending:      make(map[string]pendingAdmissionJob),
		logger:       slog.Default(),
	}
	stats := &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1}
	if err := s.persistAssignmentQuarantine(stats, 0, 0); err != nil {
		t.Fatal(err)
	}
	if err := s.resolveQuarantineFromCompleteMetadata(
		&scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 0},
		0,
		0,
	); err == nil {
		t.Fatal("aggregate zero resolved quarantine without complete metadata")
	}
	if err := s.resolveQuarantineFromCompleteMetadata(stats, 0, 1); err != nil {
		t.Fatal(err)
	}
	if s.quarantined {
		t.Fatal("complete reconstructed assignment did not resolve quarantine")
	}
	if _, err := os.Stat(filepath.Join(dir, "quarantine.json")); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("resolved quarantine file still present: %v", err)
	}
}

func TestSparseJobAssignedRecoveryMetadataIsNonAuthoritative(t *testing.T) {
	sparse := scaleset.JobMessageBase{
		JobMessageType: scaleset.JobMessageType{MessageType: scaleset.MessageTypeJobAssigned},
		WorkflowRunID:  99,
	}
	if recoveryMetadataComplete(&sparse) {
		t.Fatal("sparse JobAssigned metadata was treated as sufficient for recovery attestation")
	}

	complete := assignedCPUJob().JobMessageBase
	if !recoveryMetadataComplete(&complete) {
		t.Fatal("complete JobAssigned metadata was rejected for recovery attestation")
	}
}

func TestAssignedRecoveryAllowsMissingRunnerRequestID(t *testing.T) {
	job := assignedCPUJob().JobMessageBase
	if job.RunnerRequestID != 0 {
		t.Fatalf("test fixture unexpectedly has runner request id %d", job.RunnerRequestID)
	}
	if !recoveryMetadataComplete(&job) {
		t.Fatal("JobAssigned recovery with stable workflow/job provenance was rejected")
	}
}

func TestProvisionStatusQueryIsNonSecretAndExact(t *testing.T) {
	dir := t.TempDir()
	socketPath := filepath.Join(dir, "provisioner-status.sock")
	ln, err := net.Listen("unix", socketPath)
	if err != nil {
		t.Fatal(err)
	}
	defer ln.Close()

	received := make(chan provisionStatusRequest, 1)
	go func() {
		conn, err := ln.Accept()
		if err != nil {
			return
		}
		defer conn.Close()
		var req provisionStatusRequest
		if err := json.NewDecoder(bufio.NewReader(conn)).Decode(&req); err != nil {
			return
		}
		received <- req
		_ = json.NewEncoder(conn).Encode(provisionStatusResponse{
			SchemaVersion: 2,
			Status:        "MISSING",
			RequestID:     req.RequestID,
		})
	}()

	requestID := "01234567-89ab-5cde-8fab-0123456789ab"
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	response, err := sendProvisionStatusQuery(ctx, socketPath, requestID)
	if err != nil {
		t.Fatal(err)
	}
	if response.Status != "MISSING" {
		t.Fatalf("unexpected status %q", response.Status)
	}
	req := <-received
	if req.SchemaVersion != 2 || req.Operation != "STATUS" || req.RequestID != requestID {
		t.Fatalf("unexpected status request %#v", req)
	}
	raw, _ := json.Marshal(req)
	if strings.Contains(string(raw), "jit") || strings.Contains(string(raw), "attestation") {
		t.Fatalf("status query unexpectedly carried execution material: %s", raw)
	}
}

func TestOrphanJITRegistrationIsRemovedOnlyFromExpectedScaleSet(t *testing.T) {
	client := &fakeRunnerJITClient{
		runner: &scaleset.RunnerReference{
			ID:               77,
			Name:             "lambda-research-engine-deadbeef0001",
			RunnerScaleSetID: 1,
		},
	}
	removed, err := reconcileOrphanJITRegistration(
		context.Background(),
		client,
		"lambda-research-engine-deadbeef0001",
		1,
	)
	if err != nil {
		t.Fatal(err)
	}
	if !removed || !reflect.DeepEqual(client.removedIDs, []int64{77}) {
		t.Fatalf("orphan registration was not removed: %#v", client.removedIDs)
	}

	client.runner = &scaleset.RunnerReference{
		ID:               78,
		Name:             "lambda-research-engine-deadbeef0001",
		RunnerScaleSetID: 2,
	}
	if _, err := reconcileOrphanJITRegistration(
		context.Background(),
		client,
		"lambda-research-engine-deadbeef0001",
		1,
	); err == nil {
		t.Fatal("cross-scale-set runner registration was removed")
	}
}


type fakeScaleSetMaintenanceClient struct {
	scaleSet  *scaleset.RunnerScaleSet
	deletedID int
}

func (f *fakeScaleSetMaintenanceClient) GetRunnerScaleSet(
	context.Context,
	int,
	string,
) (*scaleset.RunnerScaleSet, error) {
	return f.scaleSet, nil
}

func (f *fakeScaleSetMaintenanceClient) DeleteRunnerScaleSet(
	_ context.Context,
	id int,
) error {
	f.deletedID = id
	f.scaleSet = nil
	return nil
}

func TestScaleSetMaintenanceDeleteRequiresExactQuiescentConfiguredScaleSet(t *testing.T) {
	cfg := config{ScaleSetName: "lambda-workspace-control"}
	client := &fakeScaleSetMaintenanceClient{
		scaleSet: &scaleset.RunnerScaleSet{
			ID:   77,
			Name: "lambda-workspace-control",
			Statistics: &scaleset.RunnerScaleSetStatistic{
				TotalRegisteredRunners: 1,
			},
		},
	}
	_, err := executeScaleSetMaintenance(
		context.Background(),
		client,
		cfg,
		scaleSetMaintenanceRequest{
			SchemaVersion:      1,
			Operation:          "DELETE",
			ExpectedScaleSetID: 77,
		},
	)
	if err == nil || !strings.Contains(err.Error(), "not quiescent") {
		t.Fatalf("non-quiescent scale set deletion was not rejected: %v", err)
	}
	if client.deletedID != 0 {
		t.Fatalf("non-quiescent scale set was deleted: %d", client.deletedID)
	}

	client.scaleSet.Statistics.TotalRegisteredRunners = 0
	if _, err := executeScaleSetMaintenance(
		context.Background(),
		client,
		cfg,
		scaleSetMaintenanceRequest{
			SchemaVersion:      1,
			Operation:          "DELETE",
			ExpectedScaleSetID: 78,
		},
	); err == nil {
		t.Fatal("wrong numeric scale-set id was accepted")
	}
	if client.deletedID != 0 {
		t.Fatalf("mismatched scale set was deleted: %d", client.deletedID)
	}

	response, err := executeScaleSetMaintenance(
		context.Background(),
		client,
		cfg,
		scaleSetMaintenanceRequest{
			SchemaVersion:      1,
			Operation:          "DELETE",
			ExpectedScaleSetID: 77,
		},
	)
	if err != nil {
		t.Fatal(err)
	}
	if response.Status != "DELETED" || response.ScaleSetID != 77 || client.deletedID != 77 {
		t.Fatalf("exact quiescent delete failed response=%#v deleted=%d", response, client.deletedID)
	}
}

func TestScaleSetMaintenanceInspectCannotSelectAnotherScaleSet(t *testing.T) {
	cfg := config{ScaleSetName: "lambda-workspace-control"}
	client := &fakeScaleSetMaintenanceClient{
		scaleSet: &scaleset.RunnerScaleSet{
			ID:   88,
			Name: "lambda-workspace-control",
			Statistics: &scaleset.RunnerScaleSetStatistic{
				TotalAssignedJobs: 0,
				TotalRunningJobs:  0,
			},
		},
	}
	response, err := executeScaleSetMaintenance(
		context.Background(),
		client,
		cfg,
		scaleSetMaintenanceRequest{
			SchemaVersion:      1,
			Operation:          "INSPECT",
			ExpectedScaleSetID: 0,
		},
	)
	if err != nil {
		t.Fatal(err)
	}
	if response.ScaleSetID != 88 || response.ScaleSetName != cfg.ScaleSetName {
		t.Fatalf("inspect identity drift: %#v", response)
	}
	if _, err := executeScaleSetMaintenance(
		context.Background(),
		client,
		cfg,
		scaleSetMaintenanceRequest{
			SchemaVersion:      1,
			Operation:          "DELETE_OTHER",
			ExpectedScaleSetID: 88,
		},
	); err == nil {
		t.Fatal("arbitrary scale-set maintenance operation accepted")
	}
}


func zeroScaleSetStats() *scaleset.RunnerScaleSetStatistic {
	return &scaleset.RunnerScaleSetStatistic{}
}

func TestResetPendingQuarantineSurvivesRecreatedScaleSetRestart(t *testing.T) {
	dir := t.TempDir()
	pendingPath := filepath.Join(
		dir,
		"reset-pending-aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.json",
	)
	pending := laneResetPendingReceipt{
		SchemaVersion:   1,
		ReceiptID:       "11111111-2222-4333-8444-555555555555",
		Status:          "RECOVERY_SCALESET_RESET_PENDING",
		ProjectID:       "workspace-control",
		Lane:            "cpu",
		ScaleSetName:    "lambda-workspace-control",
		ScaleSetID:      77,
		OldScaleSetID:   77,
		ResetGeneration: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
		ResetStartedAt:  time.Now().UTC().Format(time.RFC3339Nano),
	}
	if err := atomicWriteJSON(pendingPath, pending); err != nil {
		t.Fatal(err)
	}
	s := &scaler{
		scaleSetID:   88,
		projectID:    "workspace-control",
		lane:         "cpu",
		scaleSetName: "lambda-workspace-control",
		stateDir:     dir,
	}
	if err := s.loadQuarantine(); err != nil {
		t.Fatal(err)
	}
	if !s.quarantined || !s.recoveryPending {
		t.Fatalf("reset-pending quarantine did not survive restart: %#v", s)
	}
	if s.resetOldScaleSetID != 77 || s.scaleSetID != 88 {
		t.Fatalf("old/new scale-set identity lost: %#v", s)
	}
}

func TestResetPendingRejectsSameScaleSetIdentity(t *testing.T) {
	dir := t.TempDir()
	pendingPath := filepath.Join(
		dir,
		"reset-pending-aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.json",
	)
	pending := laneResetPendingReceipt{
		SchemaVersion:   1,
		ReceiptID:       "11111111-2222-4333-8444-555555555555",
		Status:          "RECOVERY_SCALESET_RESET_PENDING",
		ProjectID:       "workspace-control",
		Lane:            "cpu",
		ScaleSetName:    "lambda-workspace-control",
		ScaleSetID:      77,
		OldScaleSetID:   77,
		ResetGeneration: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
	}
	if err := atomicWriteJSON(pendingPath, pending); err != nil {
		t.Fatal(err)
	}
	s := &scaler{
		scaleSetID:   77,
		projectID:    "workspace-control",
		lane:         "cpu",
		scaleSetName: "lambda-workspace-control",
		stateDir:     dir,
	}
	if err := s.loadQuarantine(); err == nil {
		t.Fatal("reset pending accepted without a fresh scale-set id")
	}
}

func TestResetPendingRequiresTwoSeparatedZeroObservations(t *testing.T) {
	dir := t.TempDir()
	pendingPath := filepath.Join(
		dir,
		"reset-pending-aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.json",
	)
	if err := atomicWriteJSON(
		pendingPath,
		laneResetPendingReceipt{
			SchemaVersion:   1,
			ReceiptID:       "11111111-2222-4333-8444-555555555555",
			Status:          "RECOVERY_SCALESET_RESET_PENDING",
			ProjectID:       "workspace-control",
			Lane:            "cpu",
			ScaleSetName:    "lambda-workspace-control",
			ScaleSetID:      77,
			OldScaleSetID:   77,
			ResetGeneration: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
		},
	); err != nil {
		t.Fatal(err)
	}
	s := &scaler{
		active:             make(map[string]string),
		scaleSetID:         88,
		projectID:          "workspace-control",
		lane:               "cpu",
		scaleSetName:       "lambda-workspace-control",
		stateDir:           dir,
		pending:            make(map[string]pendingAdmissionJob),
		quarantined:        true,
		quarantineID:       "11111111-2222-4333-8444-555555555555",
		recoveryPending:    true,
		resetGeneration:    "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
		resetOldScaleSetID: 77,
		resetPendingPath:   pendingPath,
		logger:             slog.Default(),
	}
	msg := &scaleset.RunnerScaleSetMessage{Statistics: zeroScaleSetStats()}
	ready, err := s.observeResetPending(msg, 0, 0)
	if err != nil {
		t.Fatal(err)
	}
	if ready {
		t.Fatal("first zero observation opened retry gate")
	}
	firstPath := s.recoveryZeroPath()
	raw, err := os.ReadFile(firstPath)
	if err != nil {
		t.Fatal(err)
	}
	var first recoveryZeroObservation
	if err := json.Unmarshal(raw, &first); err != nil {
		t.Fatal(err)
	}
	first.ObservedAt = time.Now().UTC().Add(-16 * time.Second).Format(time.RFC3339Nano)
	if err := atomicWriteJSON(firstPath, first); err != nil {
		t.Fatal(err)
	}
	ready, err = s.observeResetPending(msg, 0, 0)
	if err != nil {
		t.Fatal(err)
	}
	if !ready || s.quarantined || s.recoveryPending {
		t.Fatalf("two separated zero observations did not open gate: ready=%v scaler=%#v", ready, s)
	}
	readyRaw, err := os.ReadFile(s.readyForSingleRetryPath())
	if err != nil {
		t.Fatal(err)
	}
	var receipt map[string]any
	if err := json.Unmarshal(readyRaw, &receipt); err != nil {
		t.Fatal(err)
	}
	if receipt["status"] != "READY_FOR_SINGLE_RETRY" {
		t.Fatalf("ready receipt status mismatch: %#v", receipt)
	}
	if int(receipt["old_scale_set_id"].(float64)) != 77 ||
		int(receipt["new_scale_set_id"].(float64)) != 88 {
		t.Fatalf("ready receipt scale-set identity mismatch: %#v", receipt)
	}
	if receipt["automatic_workflow_triggered"] != false {
		t.Fatalf("ready receipt unexpectedly claims workflow trigger: %#v", receipt)
	}
	if _, err := os.Stat(pendingPath); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("reset-pending state remained after ready proof: %v", err)
	}
}

func TestResetPendingNonzeroStateInvalidatesFirstZeroObservation(t *testing.T) {
	dir := t.TempDir()
	pendingPath := filepath.Join(
		dir,
		"reset-pending-aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.json",
	)
	s := &scaler{
		scaleSetID:         88,
		projectID:          "workspace-control",
		lane:               "cpu",
		scaleSetName:       "lambda-workspace-control",
		stateDir:           dir,
		quarantined:        true,
		quarantineID:       "11111111-2222-4333-8444-555555555555",
		recoveryPending:    true,
		resetGeneration:    "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
		resetOldScaleSetID: 77,
		resetPendingPath:   pendingPath,
		logger:             slog.Default(),
	}
	if err := atomicWriteJSON(
		s.recoveryZeroPath(),
		recoveryZeroObservation{
			SchemaVersion:   1,
			ResetGeneration: s.resetGeneration,
			ScaleSetID:      88,
			ObservedAt:      time.Now().UTC().Add(-30 * time.Second).Format(time.RFC3339Nano),
		},
	); err != nil {
		t.Fatal(err)
	}
	stats := zeroScaleSetStats()
	stats.TotalAssignedJobs = 1
	ready, err := s.observeResetPending(
		&scaleset.RunnerScaleSetMessage{Statistics: stats},
		0,
		0,
	)
	if err != nil {
		t.Fatal(err)
	}
	if ready {
		t.Fatal("nonzero reset-pending observation opened gate")
	}
	if _, err := os.Stat(s.recoveryZeroPath()); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("nonzero state did not invalidate first zero observation: %v", err)
	}
}

func TestResetPendingRefusesAvailableWorkWithoutAttestationOrAcquire(t *testing.T) {
	dir := t.TempDir()
	attestor := &neverCalledAttestor{}
	s := &scaler{
		active:             make(map[string]string),
		scaleSetID:         88,
		projectID:          "workspace-control",
		lane:               "cpu",
		scaleSetName:       "lambda-workspace-control",
		runnerPrefix:       "lambda-workspace-control-",
		stateDir:           dir,
		admissionV2:        true,
		attestor:           attestor,
		pending:            make(map[string]pendingAdmissionJob),
		quarantined:        true,
		quarantineID:       "11111111-2222-4333-8444-555555555555",
		recoveryPending:    true,
		resetGeneration:    "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
		resetOldScaleSetID: 77,
		resetPendingPath:   filepath.Join(dir, "reset-pending-aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.json"),
		logger:             slog.Default(),
	}
	available := availableCPUJob()
	if err := s.Scale(
		context.Background(),
		&scaleset.RunnerScaleSetMessage{
			Statistics:           zeroScaleSetStats(),
			JobAvailableMessages: []*scaleset.JobAvailable{available},
		},
	); err != nil {
		t.Fatal(err)
	}
	if attestor.calls != 0 {
		t.Fatalf("reset-pending lane attested available work: %d", attestor.calls)
	}
	if len(s.pending) != 0 || len(s.active) != 0 {
		t.Fatalf("reset-pending lane staged execution state: pending=%d active=%d", len(s.pending), len(s.active))
	}
	if !s.quarantined || !s.recoveryPending {
		t.Fatal("available work escaped reset-pending quarantine")
	}
}


func TestRecoveryGenerationIsConsumedByFirstAcquiredJobAndClosedOnCompletion(t *testing.T) {
	dir := t.TempDir()
	s := &scaler{
		scaleSetID:   88,
		projectID:    "workspace-control",
		lane:         "cpu",
		scaleSetName: "lambda-workspace-control",
		stateDir:     dir,
		logger:       slog.Default(),
	}
	ready := map[string]any{
		"schema_version": 1,
		"status": "READY_FOR_SINGLE_RETRY",
		"receipt_id": "11111111-2222-4333-8444-555555555555",
		"project_id": "workspace-control",
		"lane": "cpu",
		"scale_set_name": "lambda-workspace-control",
		"old_scale_set_id": 77,
		"new_scale_set_id": 88,
		"reset_generation": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
		"automatic_workflow_triggered": false,
	}
	if err := atomicWriteJSON(s.readyForSingleRetryPath(), ready); err != nil {
		t.Fatal(err)
	}
	attestation := controllerAttestation{
		WorkflowRunID: 12345,
		JobID:         "job-67890",
	}
	if err := s.consumeReadyForSingleRetry(attestation); err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(s.readyForSingleRetryPath())
	if err != nil {
		t.Fatal(err)
	}
	var acquired map[string]any
	if err := json.Unmarshal(raw, &acquired); err != nil {
		t.Fatal(err)
	}
	if acquired["status"] != "RECOVERY_RETRY_ACQUIRED" ||
		acquired["job_id"] != "job-67890" {
		t.Fatalf("recovery generation not consumed by exact job: %#v", acquired)
	}
	if int64(acquired["workflow_run_id"].(float64)) != 12345 {
		t.Fatalf("workflow run identity missing: %#v", acquired)
	}
	if err := s.consumeReadyForSingleRetry(attestation); err != nil {
		t.Fatal(err)
	}
	if err := s.consumeReadyForSingleRetry(
		controllerAttestation{
			WorkflowRunID: 54321,
			JobID:         "different-job",
		},
	); err == nil {
		t.Fatal("second different job consumed an in-flight recovery generation")
	}

	completed := &scaleset.JobCompleted{
		Result:     "Succeeded",
		RunnerName: "lambda-workspace-control-retry",
		JobMessageBase: scaleset.JobMessageBase{
			JobID: "job-67890",
		},
	}
	if err := s.completeRecoveryRetry(completed); err != nil {
		t.Fatal(err)
	}
	raw, err = os.ReadFile(s.readyForSingleRetryPath())
	if err != nil {
		t.Fatal(err)
	}
	var terminal map[string]any
	if err := json.Unmarshal(raw, &terminal); err != nil {
		t.Fatal(err)
	}
	if terminal["status"] != "RECOVERY_RETRY_COMPLETED" ||
		terminal["result"] != "Succeeded" ||
		terminal["runner_name"] != completed.RunnerName {
		t.Fatalf("recovery retry terminal receipt mismatch: %#v", terminal)
	}
}

func TestRecoveryRetryReceiptRejectsWrongScaleSetIdentity(t *testing.T) {
	dir := t.TempDir()
	s := &scaler{
		scaleSetID:   88,
		projectID:    "workspace-control",
		lane:         "cpu",
		scaleSetName: "lambda-workspace-control",
		stateDir:     dir,
		logger:       slog.Default(),
	}
	if err := atomicWriteJSON(
		s.readyForSingleRetryPath(),
		map[string]any{
			"schema_version": 1,
			"status": "READY_FOR_SINGLE_RETRY",
			"receipt_id": "11111111-2222-4333-8444-555555555555",
			"project_id": "workspace-control",
			"lane": "cpu",
			"scale_set_name": "lambda-workspace-control",
			"old_scale_set_id": 77,
			"new_scale_set_id": 99,
			"reset_generation": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
			"automatic_workflow_triggered": false,
		},
	); err != nil {
		t.Fatal(err)
	}
	if err := s.consumeReadyForSingleRetry(
		controllerAttestation{WorkflowRunID: 123, JobID: "job"},
	); err == nil {
		t.Fatal("recovery retry consumed receipt for wrong scale-set identity")
	}
}
