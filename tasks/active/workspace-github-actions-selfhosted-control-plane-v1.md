<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-selfhosted-control-plane-v1
- Title: GitHub Actions Self-Hosted Control Plane v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Eliminate routine dependence on metered GitHub-hosted runners by moving workspace-control and project CI onto bounded self-hosted Lambda execution while preserving a non-circular bootstrap authority, per-project isolation, fail-closed admission, review gates, and a clean path to GitHub organization runner groups. Also reduce operator copy/paste by making review targets and dispositions durable and GitHub-native.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 6bd20890e2bc8a44dba8a33227cbb69b3e1368fd
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Operator: execute scripts/lambda_ci_p1_bootstrap_install.py from a detached exact checkout of reviewed merge 6bd20890e2bc8a44dba8a33227cbb69b3e1368fd, with --expected-head set to that exact SHA and full output captured. Research-engine CPU must be preserved exactly in whatever reviewed stable state it occupies (active/running with ExecMainStatus=0, inactive/dead with valid nonnegative ExecMainStatus, or failed/failed with valid positive ExecMainStatus); any malformed, transitional, or changing state must abort before mutation. The other three project/lane controllers must remain active and preserved. The sole initial service mutation remains stopping automatic reconcile-controller. On success, workspace-control must remain MIGRATION_CANDIDATE_NOT_INSTALLED / PLANNED_NOT_BOUND and inactive, and automatic reconcile-controller must remain frozen. Return the complete output/receipt before any GitHub -> L0 diagnose or workspace-control activation.

## Remaining work

- Validate and independently review PR #530, then retry the rollback-safe P1 bootstrap installer only from the exact reviewed merge SHA; preserve the three healthy controllers and keep workspace-control dormant.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- PR #532 corrected stable-state research-engine CPU preservation is independently accepted and merged as workspace-control@6bd20890e2bc8a44dba8a33227cbb69b3e1368fd. The next gate is one bounded live bootstrap retry from that exact reviewed merge SHA; any transitional/changing research CPU state or any post-mutation failure must abort/rollback according to the reviewed installer.
- workspace-control activation remains separately blocked until bootstrap install passes and a real GitHub -> L0 maintenance DIAGNOSE_LANE command produces a durable accepted receipt.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
