# Workspace Control Throughput & CI Efficiency v1

Status: **evidence-backed design candidate**

Task: `tasks/active/workspace-control-throughput-ci-efficiency-v1.json`

## Purpose

Reduce avoidable control-cycle latency without weakening provenance, fail-closed
mutation semantics, authority boundaries, durable recovery, or high-consequence
validation.

The optimization target is not "fewer tests." It is:

> pay the cheapest validation cost that proves the changed state is safe, and
> escalate automatically when the changed state is ambiguous or consequential.

`research-engine` remains read-only during this design stage.

## Measured baseline

The representative slice is `research-engine` PRs #73-#77 from 2026-10-04.

### CI wall time

Final successful PR runs:

| PR | PR CI | main CI |
| --- | ---: | ---: |
| #73 | 73 s | 75 s |
| #74 | 75 s | 65 s |
| #75 | 81 s | 81 s |
| #76 | 81 s | 82 s |
| #77 | 91 s | 81 s |

The five successful PR runs total 401 s and the five immediately corresponding
main runs total 384 s: **785 s (~13.1 min)** of CI wall time for five narrow
iterations.

PR #75 also ran and failed an earlier 58 s PR workflow before the follow-up fix.
Including that failed attempt raises observed CI consumption for the slice to at
least **843 s (~14.1 min)**.

### Successful-run cost decomposition

Representative final PR #77 and its main run show the dominant costs:

| Component | PR #77 | main #77 |
| --- | ---: | ---: |
| PostgreSQL image/start | ~12.0 s | ~12.5 s |
| PostgreSQL health wait | ~6.2 s | ~6.4 s |
| checkout | ~0.8 s | ~0.8 s |
| setup-python | ~3.3 s | ~2.7 s |
| editable install | ~12.0 s | ~9.2 s |
| compile | ~0.3 s | ~0.3 s |
| pytest | ~21.8 s | ~21.0 s |
| Compose config validation | ~2.7 s | ~0.4 s |
| daemon Docker build | ~18.7 s | ~17.6 s |

These are wall-clock intervals between major workflow step boundaries from the
GitHub job logs; they are intentionally approximate rather than CPU-time claims.

The present workflow starts the PostgreSQL/pgvector service before every test
job, then always installs, compiles, runs the complete pytest suite, validates
Compose, and builds the daemon image. There is no path/risk dispatch.

### Tested-tree duplication

For each final PR run #73-#77, GitHub Actions checked out the synthetic
`refs/pull/<N>/merge` commit. The synthetic merge tree SHA was compared with
the eventual squash-merged `main` commit tree SHA:

| PR | PR synthetic merge tree == merged main tree |
| --- | --- |
| #73 | yes |
| #74 | yes |
| #75 | yes |
| #76 | yes |
| #77 | yes |

Therefore, for this five-PR sample, the immediate post-merge main run repeated
the same workflow over the exact same Git tree. It did not add tree-content
coverage. This is evidence for a tested-tree optimization condition, **not** a
general rule that post-submit CI is redundant.

If the base branch changes, the merge result changes, event-specific behavior is
material, or the actual merged tree is not proven equal to the tested tree, the
optimization does not apply.

### Orchestration overhead

The five PRs contained **23 branch commits** for five logical fixes. Most were
small file-at-a-time or concern-at-a-time commits created seconds apart before
the PR was opened. The GitHub connector already exposes the Git data API surface
needed to batch a logical mutation:

1. create blobs (independent blobs may be created in parallel);
2. create one tree from the verified base tree;
3. create one commit;
4. move the branch ref with an expected-SHA lease.

This preserves an inspectable atomic Git checkpoint while eliminating repeated
contents-API commits and tool round trips.

PR #75 also demonstrates premature PR creation cost. The PR opened on one head,
the first workflow ran for 58 s and failed, then a follow-up commit created a
second full PR run. Consolidating all known preflight fixes before opening the PR
would have avoided that first CI attempt.

Historical connector-read latency cannot be reconstructed exactly because
read/poll calls do not leave repository or Actions records. The durable evidence
does establish repeated short-interval polling. Treat connector polling overhead
as an **unmeasured positive term**, not as zero.

After a final PR check succeeds, blocking on the corresponding merged-main run
adds roughly 68-84 s from merge to main success in this sample, and roughly
79-105 s from final PR success to main success. That wait belongs on the
conversational critical path only when the next action genuinely depends on
post-submit state.

## Connector-native control-loop improvements

Use the connector surface as a transaction-like Git operation rather than a
sequence of file commits.

### Mutation batch

For one logical checkpoint:

```text
verify branch head/base tree
-> create changed-file blobs in parallel
-> create one tree containing the reviewed path set
-> create one commit
-> immediately re-read the branch head
-> update_ref to the new commit
-> reread exact resulting branch/commit/tree
```

The connector advertises an `expected_sha` lease for `update_ref`, but the
current wrapper rejects that argument during input validation. Plain
`update_ref` works. Until the wrapper is repaired, the safe connector sequence
is therefore verify-head immediately before the ref move and verify again
immediately after. Do not claim lease-protected mutation when the lease argument
was not accepted.

Do not run same-path writes concurrently. If the pre-write head check no longer
matches, reread state and reconcile instead of forcing.

### PR timing

Open/update the PR only after:

- the intended changed-path set is stable;
- cheap deterministic validation has passed;
- the branch contains the complete logical mutation batch.

If CI identifies a defect, inspect the failed job/log first, then prefer one
consolidated repair batch over multiple speculative commits.

### Status reads

Use the cheapest status surface first:

- one combined commit/status or workflow-run collection read;
- job metadata only when a run is active/failed and job identity matters;
- logs only for failure diagnosis.

Do not poll in a tight loop. For the current ~80 s baseline, independent task
work should proceed while CI runs. A second status read belongs at a semantic
decision boundary, not merely because several seconds passed.

## External practice research

The design is grounded in documented behavior rather than copied by analogy.

### GitHub tested-merge semantics

GitHub documents that `pull_request` workflows run against the PR merge ref.
Required-check rules can use strict up-to-date semantics, and merge queues
re-test required checks after applying the PR to the latest target branch and
queued changes.

References:

- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets

### Path selection, concurrency, and schedules

GitHub Actions supports changed-path filters, workflow/job concurrency with
`cancel-in-progress`, reusable workflows, and scheduled runs on the latest
default-branch commit. GitHub also warns that a workflow skipped by path filters
can leave a required check pending, so a stable required gate should not be
implemented as a required workflow that disappears entirely for low-risk paths.

References:

- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency

### Affected-graph selection

Nx's documented affected algorithm combines Git changed files with the project
dependency graph and includes dependent projects. This is the correct conceptual
model for targeted validation: path matching alone is insufficient when a shared
dependency changed.

Reference:

- https://nx.dev/docs/features/ci-features/affected

### CI cache reuse

Docker BuildKit supports external cache exporters/importers, including a GitHub
Actions cache backend, so ephemeral CI workers do not need to rebuild every layer
from cold state when inputs are unchanged.

Reference:

- https://docs.docker.com/build/cache/backends/

### Mature pre-submit/post-submit separation

Kubernetes Prow distinguishes presubmit, postsubmit, and periodic jobs, supports
changed-file selection for presubmits, and separately controls whether contexts
are required or merely reported. The relevant lesson is separation of
synchronous merge protection from broader regression/operational coverage, not
adoption of Prow itself.

References:

- https://docs.prow.k8s.io/docs/overview/
- https://docs.prow.k8s.io/docs/jobs/

## Risk-tiered validation contract

The classifier is fail-closed. If no rule proves a cheaper tier is sufficient,
escalate.

### T0 — FAST_STATIC

Purpose: immediate deterministic feedback for changes that cannot affect runtime,
database, image/deployment, security, scientific state, or shared executable
contracts.

Typical examples:

- prose-only documentation;
- task capsule state plus its derived handoff;
- comments/metadata that do not alter executable workflow semantics.

Required evidence:

- exact changed-path set;
- syntax/structural validation for changed JSON/Markdown contracts;
- task capsule JSON/Markdown synchronization when applicable;
- targeted deterministic validators for the changed artifact.

No PostgreSQL service or Docker image build is required merely because those
checks exist elsewhere.

### T1 — TARGETED_PR

Purpose: executable or test/harness changes with a bounded dependency radius.

Typical examples:

- isolated helper/script changes;
- benchmark harness behavior that does not touch production routing;
- unit-test-only changes;
- project-local code where affected dependents can be enumerated.

Required evidence:

- T0 checks;
- affected unit/static tests;
- compile/type/lint checks that cover changed executable paths;
- PR synthetic-merge validation.

Escalate to T2 if affected dependency closure is unknown.

### T2 — FULL_INTEGRATION

Purpose: changes whose failure radius crosses durable/runtime boundaries.

Force this tier for any mutation affecting or ambiguously touching:

- database schema, migrations, persistence, or PostgreSQL integration;
- daemon lifecycle or scheduler/executor lifecycle;
- Dockerfile, Compose, deployment, systemd, or container/runtime packaging;
- security, credentials, permissions, authentication, or secret-handling;
- scientific-state materialization, provenance, verification, or destructive state;
- shared control-plane contracts/schemas that can change mutation or handoff safety;
- dependency/lock/runtime version changes that can affect those boundaries;
- classifier/routing rules themselves;
- any changed path not matched by a proven lower-risk rule.

Required evidence:

- full unit/integration suite;
- real database boundary when the project defines it as canonical;
- Compose/deployment static validation when affected;
- Docker image build when packaging/runtime image semantics are affected;
- PR tested-merge identity and required checks.

### T3 — CANONICAL_REGRESSION

Purpose: preserve broad-system confidence without making every low-risk mutation
wait synchronously for the maximum suite twice.

Run on:

- scheduled/default-branch regression;
- explicit force-full request;
- release/deployment gates where canonical post-submit identity matters;
- post-submit observation for high-risk integrations;
- periodic verification that T0/T1 selection rules have not missed interactions.

T3 may reuse T2 tests, but its scheduling/critical-path semantics differ.

## Escalation and force-full rules

The decision is monotonic: a higher applicable tier wins.

`force_full=true` selects at least T2 regardless of changed paths.

Any ambiguity selects T2. In particular:

- unknown file;
- unknown dependency edge;
- classifier parse failure;
- base/head diff cannot be established;
- mixed changes spanning lower- and higher-risk groups;
- validation-plan implementation itself changes.

No user or model inference may downgrade a deterministic forced escalation
without changing and validating the governing policy.

## Stable required gate

When GitHub Actions is introduced/changed, prefer one always-present required
validation gate that:

1. computes the risk/affected plan;
2. runs or awaits the selected required jobs;
3. reports one stable success/failure result.

Do not make a path-filtered workflow itself the sole required status because
GitHub documents that skipped path-filtered workflows can remain pending.

Advisory/postsubmit/periodic jobs may be separate.

## Tested-tree and canonical-main rule

PR validation is sufficient to unblock subsequent **conversation work** when all
of the following are proven:

1. the PR workflow tested the synthetic merge result, not only the PR head;
2. all checks required for that risk tier passed;
3. the actual merged main tree is equal to the tested merge tree, **or** a merge
   queue/strict tested-latest-target mechanism establishes equivalent semantics;
4. the next action does not require a post-submit deployment, release,
   canonical-only side effect, or event-specific validation.

If any condition is false or unknown, canonical validation remains a dependency.

A post-submit regression may still run asynchronously even when it is not on the
conversation critical path. Failure remains a real failure and must be surfaced;
"asynchronous" does not mean "optional truth."

## Proposed research-engine shape after explicit authority expansion

No research-engine mutation is authorized by this document.

If a later capsule update grants authority, the evidence-supported candidate is:

- always-on risk classifier/gate;
- PR concurrency cancellation for superseded heads;
- T0/T1 jobs that avoid PostgreSQL and daemon image work when dependency closure
  proves those boundaries unaffected;
- T2 job retaining the current PostgreSQL integration, full pytest, Compose, and
  image-build checks for high-risk changes;
- BuildKit external cache for daemon image layers;
- scheduled/default-branch full regression;
- merge-queue or equivalent tested-latest-target semantics before relying on PR
  CI as the sole synchronous merge protection.

## Workspace-control implementation shape

Implement in workspace-control first:

1. a deterministic risk/validation-plan policy;
2. a small planner that accepts a changed-path set plus force-full and emits the
   selected tier, matched rules, escalations, and required checks;
3. unit tests proving low-risk selection, high-risk escalation, mixed-change
   escalation, unknown-path fail-closed behavior, and force-full behavior;
4. operator guidance for mutation batching, PR timing, status reads, and
   tested-tree/canonical dependency decisions.

The planner must be repository-neutral at the mechanism layer. Project-specific
path/risk facts belong in project-owned policy/configuration when later adopted.

## Benchmark plan

After implementation, measure at least:

1. trivial/low-risk documentation or task-state mutation;
2. moderate bounded code/test change;
3. high-risk integration/deployment change.

For each class record:

- Git mutation tool-call count and commit count;
- PR creation-to-required-validation time;
- number of CI restarts;
- selected validation tier;
- synchronous PR CI time;
- synchronous post-merge wait time;
- asynchronous/scheduled checks still executed;
- preserved provenance/checkpoint/capsule-sync invariants.

Success means lower critical-path latency for classes 1-2 with no reduction in
the required T2/T3 coverage for class 3.
