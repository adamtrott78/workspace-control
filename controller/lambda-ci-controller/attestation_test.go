package main

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/actions/scaleset"
)

const (
	testCandidateSHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
	testWorkflowHead = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
	testWorkflowBlob = "cccccccccccccccccccccccccccccccccccccccc"
)

func assignedCPUJob() *scaleset.JobAssigned {
	return &scaleset.JobAssigned{
		JobMessageBase: scaleset.JobMessageBase{
			JobMessageType:  scaleset.JobMessageType{MessageType: scaleset.MessageTypeJobAssigned},
			RunnerRequestID: 0,
			RepositoryName:  "research-engine",
			OwnerName:       "adamtrott78",
			JobID:           "broker-job-123",
			JobWorkflowRef: "adamtrott78/research-engine/.github/workflows/" +
				"lambda-ci-p5-autonomous.yml@refs/heads/main",
			JobDisplayName: "wc-admission-v1|workload=cpu-test|pr=101|" +
				"request=/lambda-ci-p5 " + testCandidateSHA,
			WorkflowRunID: 99,
			EventName:     "issue_comment",
		},
	}
}

func availableCPUJob() *scaleset.JobAvailable {
	assigned := assignedCPUJob()
	base := assigned.JobMessageBase
	base.MessageType = scaleset.MessageTypeJobAvailable
	base.RunnerRequestID = 12345
	base.JobID = ""
	return &scaleset.JobAvailable{JobMessageBase: base}
}

func fakeGitHubAttestorWithLifecycle(
	t *testing.T,
	mutatePull func(map[string]any),
	mutateRun func(map[string]any),
	mutateJob func(map[string]any),
) *githubJobAttestor {
	t.Helper()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if got := r.Header.Get("Authorization"); got != "Bearer test-token" {
			t.Fatalf("unexpected auth header %q", got)
		}
		w.Header().Set("Content-Type", "application/json")
		switch {
		case r.URL.Path == "/repos/adamtrott78/research-engine/actions/runs/99":
			payload := map[string]any{
				"id":         99,
				"head_sha":   testWorkflowHead,
				"path":       ".github/workflows/lambda-ci-p5-autonomous.yml",
				"event":      "issue_comment",
				"status":     "queued",
				"conclusion": nil,
				"actor": map[string]any{
					"login": "adamtrott78",
				},
				"triggering_actor": map[string]any{
					"login": "adamtrott78",
				},
				"repository": map[string]any{
					"full_name": "adamtrott78/research-engine",
				},
			}
			if mutateRun != nil {
				mutateRun(payload)
			}
			_ = json.NewEncoder(w).Encode(payload)
		case r.URL.Path == "/repos/adamtrott78/research-engine/actions/runs/99/jobs":
			jobPayload := map[string]any{
				"id":         777,
				"run_id":     99,
				"status":     "queued",
				"conclusion": nil,
				"name": "wc-admission-v1|workload=cpu-test|pr=101|" +
					"request=/lambda-ci-p5 " + testCandidateSHA,
			}
			if mutateJob != nil {
				mutateJob(jobPayload)
			}
			_ = json.NewEncoder(w).Encode(map[string]any{
				"total_count": 1,
				"jobs":       []map[string]any{jobPayload},
			})
		case r.URL.Path == "/repos/adamtrott78/research-engine/contents/.github/workflows/lambda-ci-p5-autonomous.yml":
			if got := r.URL.Query().Get("ref"); got != testWorkflowHead {
				t.Fatalf("unexpected workflow ref %q", got)
			}
			_ = json.NewEncoder(w).Encode(map[string]any{
				"type": "file",
				"path": ".github/workflows/lambda-ci-p5-autonomous.yml",
				"sha":  testWorkflowBlob,
			})
		case r.URL.Path == "/repos/adamtrott78/research-engine/pulls/101":
			payload := map[string]any{
				"number": 101,
				"state":  "open",
				"head": map[string]any{
					"sha": testCandidateSHA,
					"repo": map[string]any{
						"full_name": "adamtrott78/research-engine",
					},
				},
			}
			if mutatePull != nil {
				mutatePull(payload)
			}
			_ = json.NewEncoder(w).Encode(payload)
		default:
			http.NotFound(w, r)
		}
	}))
	t.Cleanup(server.Close)
	return &githubJobAttestor{
		owner:       "adamtrott78",
		repo:        "research-engine",
		apiBase:     server.URL,
		httpClient:  server.Client(),
		tokenSource: fixedTokenSource("test-token"),
		now: func() time.Time {
			return time.Date(2026, 10, 6, 20, 30, 0, 987654321, time.UTC)
		},
	}
}

func fakeGitHubAttestor(t *testing.T, mutatePull func(map[string]any)) *githubJobAttestor {
	return fakeGitHubAttestorWithLifecycle(t, mutatePull, nil, nil)
}

func TestAdmissionDisplayClaimIsExact(t *testing.T) {
	pr, command, sha, err := parseAdmissionDisplayClaim(
		"wc-admission-v1|workload=cpu-test|pr=101|request=/lambda-ci-p5 "+testCandidateSHA,
		"cpu-test",
	)
	if err != nil {
		t.Fatal(err)
	}
	if pr != 101 || command != "/lambda-ci-p5" || sha != testCandidateSHA {
		t.Fatalf("unexpected claim pr=%d command=%s sha=%s", pr, command, sha)
	}

	reasoner := "wc-admission-v1|workload=gpu-experiment-public|pr=282|request=/lambda-reasoner-probe " +
		testCandidateSHA + " qwen35-9b-q6-resource"
	pr, command, sha, err = parseAdmissionDisplayClaim(reasoner, "gpu-experiment-public")
	if err != nil || pr != 282 || command != "/lambda-reasoner-probe" || sha != testCandidateSHA {
		t.Fatalf("resource-probe claim rejected pr=%d command=%q sha=%q err=%v", pr, command, sha, err)
	}

	for _, invalid := range []string{
		"wc-admission-v1|workload=gpu-small|pr=101|request=/lambda-ci-p5 " + testCandidateSHA,
		"wc-admission-v1|workload=cpu-test|pr=101|request=/lambda-ci-p5 " + testCandidateSHA + " extra second",
		"wc-admission-v1|workload=cpu-test|pr=101|request=/lambda-ci-p5 " + testCandidateSHA + " bad!",
		"wc-admission-v1|workload=cpu-test|pr=101|request=/lambda-ci-p5 zzz",
	} {
		if _, _, _, err := parseAdmissionDisplayClaim(invalid, "cpu-test"); err == nil {
			t.Fatalf("invalid claim accepted: %q", invalid)
		}
	}
}

func TestAdmissionClaimParserCarriesGenericRouteCommandWithoutGrantingAuthority(t *testing.T) {
	for _, tc := range []struct{route,command string}{
		{"cpu-test","/lambda-ci-p5"},
		{"model-eval-local-extract-wave1","/lambda-ci-local-extract-wave1"},
		{"padataset-rf-benchmark-7","/lambda-ci-rf-benchmark"},
	} {
		display := "wc-admission-v1|workload="+tc.route+"|pr=101|request="+tc.command+" "+testCandidateSHA
		pr,command,sha,err := parseAdmissionDisplayClaim(display,tc.route)
		if err != nil || pr!=101 || command!=tc.command || sha!=testCandidateSHA { t.Fatalf("claim drift pr=%d command=%q sha=%q err=%v",pr,command,sha,err) }
	}
	for _, invalid := range []string{
		"wc-admission-v1|workload=cpu-test|pr=101|request=not-a-command "+testCandidateSHA,
		"wc-admission-v1|workload=cpu-test|pr=101|request=/X "+testCandidateSHA,
	} {
		if _,_,_,err:=parseAdmissionDisplayClaim(invalid,"cpu-test"); err==nil { t.Fatalf("invalid claim accepted %q",invalid) }
	}
}

func TestGitHubAttestorBindsRunBlobAndOpenPRHead(t *testing.T) {
	attestor := fakeGitHubAttestor(t, nil)
	att, err := attestor.Attest(
		context.Background(),
		&availableCPUJob().JobMessageBase,
		"lambda-research-engine",
		"cpu-test",
	)
	if err != nil {
		t.Fatal(err)
	}
	if att.SchemaVersion != 2 ||
		att.JobMessageType != string(scaleset.MessageTypeJobAvailable) ||
		att.JobID != "777" ||
		att.CandidateSHA != testCandidateSHA ||
		att.WorkflowDefaultBranchCommitSHA != testWorkflowHead ||
		att.WorkflowBlobSHA != testWorkflowBlob ||
		att.PRState != "open" ||
		att.PRHeadRepository != "adamtrott78/research-engine" ||
		att.CandidateVerification != "PR_HEAD_MATCH" {
		t.Fatalf("unexpected attestation: %#v", att)
	}
	if att.ActorLogin != "adamtrott78" || att.TriggeringActorLogin != "adamtrott78" {
		t.Fatalf("actor binding missing: %#v", att)
	}
	if att.VerifiedAt != "2026-10-06T20:30:00.987654Z" {
		t.Fatalf("verified_at is not Python-compatible RFC3339 microseconds: %q", att.VerifiedAt)
	}
}

func TestGitHubAttestorRejectsClosedOrForkPR(t *testing.T) {
	closed := fakeGitHubAttestor(t, func(payload map[string]any) {
		payload["state"] = "closed"
	})
	if _, err := closed.Attest(
		context.Background(),
		&assignedCPUJob().JobMessageBase,
		"lambda-research-engine",
		"cpu-test",
	); err == nil {
		t.Fatal("closed PR was attested")
	}

	fork := fakeGitHubAttestor(t, func(payload map[string]any) {
		head := payload["head"].(map[string]any)
		head["repo"] = map[string]any{"full_name": "attacker/fork"}
	})
	if _, err := fork.Attest(
		context.Background(),
		&assignedCPUJob().JobMessageBase,
		"lambda-research-engine",
		"cpu-test",
	); err == nil {
		t.Fatal("fork PR head was attested")
	}
}

func TestGitHubAttestorRejectsCandidateMismatch(t *testing.T) {
	mismatch := fakeGitHubAttestor(t, func(payload map[string]any) {
		head := payload["head"].(map[string]any)
		head["sha"] = strings.Repeat("d", 40)
	})
	if _, err := mismatch.Attest(
		context.Background(),
		&assignedCPUJob().JobMessageBase,
		"lambda-research-engine",
		"cpu-test",
	); err == nil {
		t.Fatal("candidate mismatch was attested")
	}
}

func TestGitHubAttestorRejectsTerminalRunAndJob(t *testing.T) {
	terminalRun := fakeGitHubAttestorWithLifecycle(
		t,
		nil,
		func(payload map[string]any) {
			payload["status"] = "completed"
			payload["conclusion"] = "cancelled"
		},
		nil,
	)
	_, err := terminalRun.Attest(
		context.Background(),
		&assignedCPUJob().JobMessageBase,
		"lambda-research-engine",
		"cpu-test",
	)
	if err == nil || !errors.Is(err, errTerminalWorkflowJob) {
		t.Fatalf("terminal workflow run was not rejected with sentinel: %v", err)
	}

	terminalJob := fakeGitHubAttestorWithLifecycle(
		t,
		nil,
		nil,
		func(payload map[string]any) {
			payload["status"] = "completed"
			payload["conclusion"] = "cancelled"
		},
	)
	_, err = terminalJob.Attest(
		context.Background(),
		&assignedCPUJob().JobMessageBase,
		"lambda-research-engine",
		"cpu-test",
	)
	if err == nil || !errors.Is(err, errTerminalWorkflowJob) {
		t.Fatalf("terminal workflow job was not rejected with sentinel: %v", err)
	}
}

func TestDeterministicAdmissionIDsAreRecoveryStable(t *testing.T) {
	available := controllerAttestation{
		Repository:"adamtrott78/research-engine", ScaleSetName:"lambda-research-engine",
		JobMessageType:string(scaleset.MessageTypeJobAvailable), RunnerRequestID:12345,
		WorkflowRunID:99, JobID:"777",
		JobDisplayName:"wc-admission-v1|workload=cpu-test|pr=101|request=/lambda-ci-p5 "+testCandidateSHA,
		CandidateSHA:testCandidateSHA, VerifiedAt:"2026-10-06T20:30:00Z",
	}
	firstRequest,firstRunner,err:=deterministicAdmissionExecutionIDs("lambda-research-engine-","cpu-test",available)
	if err!=nil { t.Fatal(err) }
	assigned:=available; assigned.JobMessageType=string(scaleset.MessageTypeJobAssigned); assigned.RunnerRequestID=0; assigned.VerifiedAt="2026-10-06T20:31:00Z"
	secondRequest,secondRunner,err:=deterministicAdmissionExecutionIDs("lambda-research-engine-","cpu-test",assigned)
	if err!=nil { t.Fatal(err) }
	if firstRequest!=secondRequest || firstRunner!=secondRunner { t.Fatalf("identity drift %q/%q %q/%q",firstRequest,secondRequest,firstRunner,secondRunner) }
	if !strings.HasPrefix(firstRunner,"lambda-research-engine-") { t.Fatalf("unexpected runner %q",firstRunner) }
}

func TestDeterministicRunnerUsesConfiguredProjectLanePrefixIndependentOfRoute(t *testing.T) {
	for _, tc := range []struct{prefix,route,repo,scaleSet string}{
		{"lambda-research-engine-gpu-","model-eval-single-gpu","adamtrott78/research-engine","lambda-research-engine-gpu"},
		{"lambda-research-engine-gpu-","model-eval-local-extract-wave1","adamtrott78/research-engine","lambda-research-engine-gpu"},
		{"lambda-padataset-gpu-","padataset-rf-benchmark-7","adamtrott78/PADataset","lambda-padataset-gpu"},
	} {
		att:=controllerAttestation{Repository:tc.repo,ScaleSetName:tc.scaleSet,JobMessageType:string(scaleset.MessageTypeJobAvailable),RunnerRequestID:12345,WorkflowRunID:99,JobID:"778",JobDisplayName:"wc-admission-v1|workload="+tc.route+"|pr=101|request=/lambda-ci-example "+testCandidateSHA,CandidateSHA:testCandidateSHA,VerifiedAt:"2026-10-20T00:00:00Z"}
		_,runner,err:=deterministicAdmissionExecutionIDs(tc.prefix,tc.route,att)
		if err!=nil || !strings.HasPrefix(runner,tc.prefix) { t.Fatalf("runner prefix failed %#v runner=%q err=%v",tc,runner,err) }
	}
}

func TestProvisionRequestV2HasNoProfileAuthority(t *testing.T) {
	req := provisionRequestV2{
		SchemaVersion: 2,
		RequestID:     "01234567-89ab-5cde-8fab-0123456789ab",
		ProjectID:     "research-engine",
		WorkloadClass: "cpu-test",
		RunnerName:    "lambda-research-engine-abcdef123456",
		JITConfig:     "opaque",
		Attestation: controllerAttestation{
			SchemaVersion: 2,
		},
	}
	raw, err := json.Marshal(req)
	if err != nil {
		t.Fatal(err)
	}
	var got map[string]any
	if err := json.Unmarshal(raw, &got); err != nil {
		t.Fatal(err)
	}
	if _, ok := got["profile"]; ok {
		t.Fatal("v2 controller request unexpectedly contains profile authority")
	}
	want := []string{
		"attestation",
		"jit_config",
		"project_id",
		"request_id",
		"runner_name",
		"schema_version",
		"workload_class",
	}
	gotKeys := make([]string, 0, len(got))
	for _, key := range want {
		if _, ok := got[key]; ok {
			gotKeys = append(gotKeys, key)
		}
	}
	if !reflect.DeepEqual(gotKeys, want) || len(got) != len(want) {
		t.Fatalf("unexpected v2 request schema: %#v", got)
	}
}

func TestTrustedWorkflowPathRejectsNonDefaultBranch(t *testing.T) {
	if _, err := trustedWorkflowPath(
		"adamtrott78/research-engine/.github/workflows/lambda-ci-p5-autonomous.yml@refs/pull/101/merge",
		"adamtrott78",
		"research-engine",
	); err == nil {
		t.Fatal("non-default-branch workflow ref was accepted")
	}
}

func TestGitHubAttestorAcceptsAssignedRecoveryWithoutRunnerRequestID(t *testing.T) {
	attestor := fakeGitHubAttestor(t, nil)
	att, err := attestor.Attest(
		context.Background(),
		&assignedCPUJob().JobMessageBase,
		"lambda-research-engine",
		"cpu-test",
	)
	if err != nil {
		t.Fatal(err)
	}
	if att.JobMessageType != string(scaleset.MessageTypeJobAssigned) ||
		att.RunnerRequestID != 0 ||
		att.JobID != "777" {
		t.Fatalf("unexpected recovery attestation: %#v", att)
	}
}
