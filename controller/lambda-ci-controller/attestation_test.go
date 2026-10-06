package main

import (
	"context"
	"encoding/json"
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
			RunnerRequestID: 12345,
			RepositoryName:  "research-engine",
			OwnerName:       "adamtrott78",
			JobID:           "job-123",
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
	return &scaleset.JobAvailable{JobMessageBase: assigned.JobMessageBase}
}

func fakeGitHubAttestor(t *testing.T, mutatePull func(map[string]any)) *githubJobAttestor {
	t.Helper()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if got := r.Header.Get("Authorization"); got != "Bearer test-token" {
			t.Fatalf("unexpected auth header %q", got)
		}
		w.Header().Set("Content-Type", "application/json")
		switch {
		case r.URL.Path == "/repos/adamtrott78/research-engine/actions/runs/99":
			_ = json.NewEncoder(w).Encode(map[string]any{
				"id":       99,
				"head_sha": testWorkflowHead,
				"path":     ".github/workflows/lambda-ci-p5-autonomous.yml",
				"event":    "issue_comment",
				"actor": map[string]any{
					"login": "adamtrott78",
				},
				"triggering_actor": map[string]any{
					"login": "adamtrott78",
				},
				"repository": map[string]any{
					"full_name": "adamtrott78/research-engine",
				},
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
			return time.Date(2026, 10, 6, 20, 30, 0, 0, time.UTC)
		},
	}
}

func TestAdmissionDisplayClaimIsExact(t *testing.T) {
	pr, sha, err := parseAdmissionDisplayClaim(
		"wc-admission-v1|workload=cpu-test|pr=101|request=/lambda-ci-p5 "+testCandidateSHA,
		"cpu-test",
		"/lambda-ci-p5",
	)
	if err != nil {
		t.Fatal(err)
	}
	if pr != 101 || sha != testCandidateSHA {
		t.Fatalf("unexpected claim pr=%d sha=%s", pr, sha)
	}

	for _, invalid := range []string{
		"wc-admission-v1|workload=gpu-small|pr=101|request=/lambda-ci-p5 " + testCandidateSHA,
		"wc-admission-v1|workload=cpu-test|pr=101|request=/lambda-ci-p5 " + testCandidateSHA + " extra",
		"wc-admission-v1|workload=cpu-test|pr=101|request=/lambda-ci-p5 zzz",
	} {
		if _, _, err := parseAdmissionDisplayClaim(invalid, "cpu-test", "/lambda-ci-p5"); err == nil {
			t.Fatalf("invalid claim accepted: %q", invalid)
		}
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
	if att.CandidateSHA != testCandidateSHA ||
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

func TestDeterministicAdmissionIDsAreRecoveryStable(t *testing.T) {
	att := controllerAttestation{
		Repository:      "adamtrott78/research-engine",
		RunnerRequestID: 12345,
		WorkflowRunID:   99,
		JobID:           "job-123",
		CandidateSHA:    testCandidateSHA,
		VerifiedAt:      "2026-10-06T20:30:00Z",
	}
	firstRequest, firstRunner, err := deterministicAdmissionExecutionIDs("cpu-test", att)
	if err != nil {
		t.Fatal(err)
	}
	att.VerifiedAt = "2026-10-06T20:31:00Z"
	secondRequest, secondRunner, err := deterministicAdmissionExecutionIDs("cpu-test", att)
	if err != nil {
		t.Fatal(err)
	}
	if firstRequest != secondRequest || firstRunner != secondRunner {
		t.Fatalf(
			"recovery identity drift request=%q/%q runner=%q/%q",
			firstRequest,
			secondRequest,
			firstRunner,
			secondRunner,
		)
	}
	if !strings.HasPrefix(firstRunner, "lambda-research-engine-") {
		t.Fatalf("unexpected deterministic runner %q", firstRunner)
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
			SchemaVersion: 1,
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
