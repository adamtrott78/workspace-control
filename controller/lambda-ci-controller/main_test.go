package main

import (
	"bufio"
	"context"
	"encoding/json"
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

func TestPilotConstantsAreFixed(t *testing.T) {
	if defaultProjectID != "research-engine" ||
		defaultProfile != "cpu-test" ||
		gpuProfile != "gpu-small" ||
		modelEvalWorkload != "model-eval-single-gpu" ||
		dualModelEvalWorkload != "model-eval-dual-gpu" ||
		localExtractWave1Workload != "model-eval-local-extract-wave1" {
		t.Fatal("pilot authority changed")
	}
	if defaultScaleSetName != "lambda-research-engine" || gpuScaleSetName != "lambda-research-engine-gpu" || maxRunners != 1 {
		t.Fatal("pilot scale-set capacity changed")
	}
	if !controllerMappingAllowed(defaultScaleSetName, defaultProfile) {
		t.Fatal("CPU controller mapping rejected")
	}
	if !controllerMappingAllowed(gpuScaleSetName, gpuProfile) {
		t.Fatal("GPU controller mapping rejected")
	}
	if controllerMappingAllowed(defaultScaleSetName, gpuProfile) ||
		controllerMappingAllowed(gpuScaleSetName, defaultProfile) ||
		controllerMappingAllowed("lambda-research-engine-heavy", "gpu-heavy") {
		t.Fatal("unexpected controller mapping accepted")
	}
}

func TestWorkloadSelectionStaysWithinControllerProfile(t *testing.T) {
	cpuClaim := "wc-admission-v1|workload=cpu-test|pr=101|request=/lambda-ci-p5 " + strings.Repeat("a", 40)
	got, err := workloadForDisplayClaim(defaultProfile, cpuClaim)
	if err != nil || got != defaultProfile {
		t.Fatalf("CPU workload selection failed got=%q err=%v", got, err)
	}

	gpuClaim := "wc-admission-v1|workload=gpu-small|pr=101|request=/lambda-ci-p5-gpu " + strings.Repeat("a", 40)
	got, err = workloadForDisplayClaim(gpuProfile, gpuClaim)
	if err != nil || got != gpuProfile {
		t.Fatalf("GPU workload selection failed got=%q err=%v", got, err)
	}

	modelClaim := "wc-admission-v1|workload=model-eval-single-gpu|pr=101|request=/lambda-ci-qwen35-pilot " + strings.Repeat("a", 40)
	got, err = workloadForDisplayClaim(gpuProfile, modelClaim)
	if err != nil || got != modelEvalWorkload {
		t.Fatalf("model-eval workload selection failed got=%q err=%v", got, err)
	}

	dualModelClaim := "wc-admission-v1|workload=model-eval-dual-gpu|pr=101|request=/lambda-ci-qwen35-dual-pilot " + strings.Repeat("a", 40)
	got, err = workloadForDisplayClaim(gpuProfile, dualModelClaim)
	if err != nil || got != dualModelEvalWorkload {
		t.Fatalf("dual model-eval workload selection failed got=%q err=%v", got, err)
	}

	wave1Claim := "wc-admission-v1|workload=model-eval-local-extract-wave1|pr=101|request=/lambda-ci-local-extract-wave1 " + strings.Repeat("a", 40)
	got, err = workloadForDisplayClaim(gpuProfile, wave1Claim)
	if err != nil || got != localExtractWave1Workload {
		t.Fatalf("Wave 1 workload selection failed got=%q err=%v", got, err)
	}

	if _, err := workloadForDisplayClaim(defaultProfile, modelClaim); err == nil {
		t.Fatal("CPU controller accepted model-eval workload")
	}
	if _, err := workloadForDisplayClaim(defaultProfile, wave1Claim); err == nil {
		t.Fatal("CPU controller accepted Wave 1 workload")
	}
	if _, err := workloadForDisplayClaim(gpuProfile, "wc-admission-v1|workload=gpu-heavy|pr=101|request=x "+strings.Repeat("a", 40)); err == nil {
		t.Fatal("GPU controller accepted gpu-heavy workload")
	}
}

func TestRunnerNamesAreProfileScoped(t *testing.T) {
	cpu, err := runnerName(defaultProfile)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(cpu, "lambda-research-engine-") || strings.HasPrefix(cpu, "lambda-research-engine-gpu-") {
		t.Fatalf("unexpected CPU runner name %q", cpu)
	}

	gpu, err := runnerName(gpuProfile)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(gpu, "lambda-research-engine-gpu-") {
		t.Fatalf("unexpected GPU runner name %q", gpu)
	}
	if _, err := runnerName("gpu-heavy"); err == nil {
		t.Fatal("gpu-heavy runner name accepted")
	}
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


func TestAdmissionV2RequiresExplicitYes(t *testing.T) {
	for _, key := range []string{
		"WORKSPACE_CI_GITHUB_URL",
		"WORKSPACE_CI_SCALESET_NAME",
		"WORKSPACE_CI_PROJECT_ID",
		"WORKSPACE_CI_PROFILE",
		"WORKSPACE_CI_PROVISIONER_SOCKET",
		"WORKSPACE_CI_APP_CLIENT_ID",
		"WORKSPACE_CI_APP_INSTALLATION_ID",
		"WORKSPACE_CI_APP_PRIVATE_KEY_FILE",
	} {
		t.Setenv(key, "")
	}
	t.Setenv("WORKSPACE_CI_PAT_FILE", "/tmp/controller-token-for-config-test")
	t.Setenv("WORKSPACE_CI_ADMISSION_V2_ENABLED", "")
	cfg, err := loadConfig()
	if err != nil {
		t.Fatal(err)
	}
	if cfg.AdmissionV2 {
		t.Fatal("admission v2 enabled without explicit YES")
	}

	t.Setenv("WORKSPACE_CI_ADMISSION_V2_ENABLED", "YES")
	cfg, err = loadConfig()
	if err != nil {
		t.Fatal(err)
	}
	if !cfg.AdmissionV2 {
		t.Fatal("explicit admission v2 YES was ignored")
	}

	t.Setenv("WORKSPACE_CI_ADMISSION_V2_ENABLED", "true")
	if _, err := loadConfig(); err == nil {
		t.Fatal("non-canonical admission v2 flag was accepted")
	}
}

func TestAdmissionV2CanProvisionFromPreAttestedJobAvailable(t *testing.T) {
	stats := &scaleset.RunnerScaleSetStatistic{
		TotalAvailableJobs: 1,
		TotalAcquiredJobs:  0,
		TotalAssignedJobs:  0,
	}
	if got := desiredRunnerTarget(stats, 1); got != 1 {
		t.Fatalf("pre-attested JobAvailable did not create runner target: %d", got)
	}
	if got := desiredRunnerTarget(stats, 0); got != 0 {
		t.Fatalf("unattested available job unexpectedly created runner target: %d", got)
	}
}

func TestAdmissionV2TargetRemainsBounded(t *testing.T) {
	stats := &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 99}
	if got := desiredRunnerTarget(stats, 99); got != maxRunners {
		t.Fatalf("target exceeded maxRunners: %d", got)
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
