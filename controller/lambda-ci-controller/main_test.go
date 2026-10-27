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
	if !s.quarantined || s.quarantineID == "" {
		t.Fatalf("assignment divergence did not quarantine lane: %#v", s)
	}
	if _, err := os.Stat(filepath.Join(dir, "quarantine.json")); err != nil {
		t.Fatalf("durable quarantine receipt missing: %v", err)
	}

	available := availableCPUJob()
	if err := s.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics:         &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 0},
		JobAvailableMessages: []scaleset.JobAvailable{*available},
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
