package main

import (
	"context"
	"encoding/json"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func newRESTVerifierTestServer(
	t *testing.T,
	actor string,
	jobLabels []string,
) (*httptest.Server, *githubVerifier) {
	t.Helper()
	policy := testPolicy()
	headSHA := strings.Repeat("d", 40)
	workflowSHA := strings.Repeat("c", 40)

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch {
		case r.URL.Path == "/repos/adamtrott78/workspace-control/actions/runs":
			status := r.URL.Query().Get("status")
			if status == "queued" {
				_ = json.NewEncoder(w).Encode(map[string]any{
					"workflow_runs": []any{map[string]any{
						"id":          501,
						"head_sha":    headSHA,
						"head_branch": "main",
						"path":        ".github/workflows/control.yml",
						"event":       "issue_comment",
						"status":      "queued",
						"actor": map[string]any{
							"login": actor,
						},
						"triggering_actor": map[string]any{
							"login": actor,
						},
						"repository": map[string]any{
							"full_name": "adamtrott78/workspace-control",
						},
					}},
				})
				return
			}
			_ = json.NewEncoder(w).Encode(map[string]any{"workflow_runs": []any{}})
			return

		case r.URL.Path == "/repos/adamtrott78/workspace-control/actions/runs/501/jobs":
			_ = json.NewEncoder(w).Encode(map[string]any{
				"jobs": []any{map[string]any{
					"id":          601,
					"status":      "queued",
					"labels":      jobLabels,
					"runner_id":   0,
					"runner_name": "",
				}},
			})
			return

		case r.URL.Path == "/repos/adamtrott78/workspace-control/contents/.github/workflows/control.yml":
			if got := r.URL.Query().Get("ref"); got != headSHA {
				t.Fatalf("content ref=%q want=%q", got, headSHA)
			}
			_ = json.NewEncoder(w).Encode(map[string]any{
				"type": "file",
				"path": ".github/workflows/control.yml",
				"sha":  workflowSHA,
			})
			return

		default:
			t.Fatalf("unexpected REST request: %s?%s", r.URL.Path, r.URL.RawQuery)
		}
	}))
	t.Cleanup(server.Close)

	verifier := &githubVerifier{
		policy:     policy,
		owner:      "adamtrott78",
		repo:       "workspace-control",
		apiBase:    server.URL,
		httpClient: server.Client(),
		tokens:     fixedTokenSource("test-token"),
		logger:     slog.New(slog.DiscardHandler),
	}
	return server, verifier
}

func TestDiscoverTrustedDemandUsesRESTJobIdentity(t *testing.T) {
	_, verifier := newRESTVerifierTestServer(
		t,
		"adamtrott78",
		[]string{"lambda-v3-wc-control"},
	)

	jobs, safe, reason, err := verifier.DiscoverTrustedDemand(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if !safe || reason != "" {
		t.Fatalf("trusted REST demand rejected: safe=%v reason=%q", safe, reason)
	}
	if len(jobs) != 1 {
		t.Fatalf("REST candidate count=%d want=1", len(jobs))
	}
	job := jobs[0]
	if job.GitHubJobID != 601 ||
		job.RunnerRequestID != 601 ||
		job.WorkflowRunID != 501 ||
		job.AuthoritySource != "REST_ACTIVE_JOB_SET" ||
		job.WorkflowPath != ".github/workflows/control.yml" ||
		job.WorkflowBlobSHA != strings.Repeat("c", 40) {
		t.Fatalf("REST verified job mismatch: %#v", job)
	}
}

func TestDiscoverTrustedDemandRejectsUntrustedTargetLabelRun(t *testing.T) {
	_, verifier := newRESTVerifierTestServer(
		t,
		"mallory",
		[]string{"lambda-v3-wc-control"},
	)

	jobs, safe, reason, err := verifier.DiscoverTrustedDemand(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if safe || len(jobs) != 0 || !strings.Contains(reason, "actor is not allowed") {
		t.Fatalf("untrusted target-label job was not rejected: safe=%v jobs=%#v reason=%q", safe, jobs, reason)
	}
}

func TestDiscoverTrustedDemandIgnoresJobsForOtherLabels(t *testing.T) {
	_, verifier := newRESTVerifierTestServer(
		t,
		"mallory",
		[]string{"ubuntu-latest"},
	)

	jobs, safe, reason, err := verifier.DiscoverTrustedDemand(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if !safe || reason != "" || len(jobs) != 0 {
		t.Fatalf("unrelated job affected class admission: safe=%v jobs=%#v reason=%q", safe, jobs, reason)
	}
}
