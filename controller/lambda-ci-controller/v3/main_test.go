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


func TestGitHubRESTStatusIsTransientDistinguishesRateLimit403(t *testing.T) {
	cases := []struct {
		name   string
		status int
		header http.Header
		body   string
		want   bool
	}{
		{
			name:   "primary rate limit header",
			status: http.StatusForbidden,
			header: http.Header{"X-RateLimit-Remaining": []string{"0"}},
			want:   true,
		},
		{
			name:   "primary rate limit body",
			status: http.StatusForbidden,
			body:   `{"message":"API rate limit exceeded for user ID 61768467"}`,
			want:   true,
		},
		{
			name:   "secondary rate limit",
			status: http.StatusForbidden,
			body:   `{"message":"You have exceeded a secondary rate limit."}`,
			want:   true,
		},
		{
			name:   "retry after",
			status: http.StatusForbidden,
			header: http.Header{"Retry-After": []string{"60"}},
			want:   true,
		},
		{
			name:   "ordinary forbidden stays fail closed",
			status: http.StatusForbidden,
			body:   `{"message":"Resource not accessible by integration"}`,
			want:   false,
		},
		{
			name:   "too many requests",
			status: http.StatusTooManyRequests,
			want:   true,
		},
		{
			name:   "server error",
			status: http.StatusServiceUnavailable,
			want:   true,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			resp := &http.Response{StatusCode: tc.status, Header: tc.header}
			if got := githubRESTStatusIsTransient(resp, []byte(tc.body)); got != tc.want {
				t.Fatalf("githubRESTStatusIsTransient()=%v want=%v", got, tc.want)
			}
		})
	}
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


func TestDiscoverTrustedDemandFallsBackToUnfilteredRecentRuns(t *testing.T) {
	policy := testPolicy()
	headSHA := strings.Repeat("d", 40)
	workflowSHA := strings.Repeat("c", 40)

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch {
		case r.URL.Path == "/repos/adamtrott78/workspace-control/actions/runs":
			if r.URL.Query().Get("status") != "" {
				_ = json.NewEncoder(w).Encode(map[string]any{"workflow_runs": []any{}})
				return
			}
			_ = json.NewEncoder(w).Encode(map[string]any{
				"workflow_runs": []any{
					map[string]any{
						"id":          501,
						"head_sha":    headSHA,
						"head_branch": "main",
						"path":        ".github/workflows/control.yml",
						"event":       "issue_comment",
						"status":      "queued",
						"actor": map[string]any{
							"login": "adamtrott78",
						},
						"triggering_actor": map[string]any{
							"login": "adamtrott78",
						},
						"repository": map[string]any{
							"full_name": "adamtrott78/workspace-control",
						},
					},
					map[string]any{
						"id":     502,
						"status": "completed",
					},
				},
			})
			return

		case r.URL.Path == "/repos/adamtrott78/workspace-control/actions/runs/501/jobs":
			_ = json.NewEncoder(w).Encode(map[string]any{
				"jobs": []any{map[string]any{
					"id":          601,
					"status":      "queued",
					"labels":      []string{"lambda-v3-wc-control"},
					"runner_id":   0,
					"runner_name": "",
				}},
			})
			return

		case r.URL.Path == "/repos/adamtrott78/workspace-control/contents/.github/workflows/control.yml":
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
	defer server.Close()

	verifier := &githubVerifier{
		policy:     policy,
		owner:      "adamtrott78",
		repo:       "workspace-control",
		apiBase:    server.URL,
		httpClient: server.Client(),
		tokens:     fixedTokenSource("test-token"),
		logger:     slog.New(slog.DiscardHandler),
	}

	jobs, safe, reason, err := verifier.DiscoverTrustedDemand(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if !safe || reason != "" {
		t.Fatalf("fallback REST demand rejected: safe=%v reason=%q", safe, reason)
	}
	if len(jobs) != 1 || jobs[0].GitHubJobID != 601 || jobs[0].WorkflowRunID != 501 {
		t.Fatalf("fallback REST candidate mismatch: %#v", jobs)
	}
}
