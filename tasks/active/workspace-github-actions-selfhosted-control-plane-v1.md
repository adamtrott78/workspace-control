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
- Remote branch: gitrunner-p1-bootstrap-shared-restart-recovery
- Remote checkpoint: 7e8aefa6f759b11a6de4e087cdb050267c6aae34
- Remote verified: false

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Request fresh independent corrected-head review of PR #536 after closing BF-1. Verify no_active_project_execution() requires systemctl list-units returncode exactly 0 before interpreting stdout, so any nonzero result fails closed. Verify regression coverage proves a nonzero pre-recovery inspection aborts before the exact three-controller systemctl start mutation and a nonzero post-start inspection rejects final certification. Regression-check all previously accepted PR #536 boundaries: maintenance supplementary-group correction, dependency-stop restoration, research-engine CPU preservation-only behavior, exact source provenance, exact incident-state predicates, and exact three-controller mutation scope. Do not merge or mutate Lambda until NO_BLOCKING_FINDING is recorded on the exact final head.

## Remaining work

- Validate and independently review PR #530, then retry the rollback-safe P1 bootstrap installer only from the exact reviewed merge SHA; preserve the three healthy controllers and keep workspace-control dormant.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- Independent review comment 6436235254 on PR #536 old head f31938895203a4867207138bd9c40bac061a1992 found BF-1: incident recovery accepted systemctl list-units rc=1, allowing execution-state inspection to fail open before mutation and during final certification. That old head must not be merged or used for Lambda mutation.
- BF-1 is corrected on PR #536 code/test head 7e8aefa6f759b11a6de4e087cdb050267c6aae34: execution-state inspection now requires returncode == 0 before stdout is interpreted. Dedicated regressions prove nonzero inspection aborts before any controller start and also rejects post-start final certification. Exact validation run 40467491614 / job 122066437641 / run #932 completed SUCCESS. Fresh independent corrected-head review remains required before merge or live recovery.
- No bootstrap retry, workspace-control activation, reconciliation, L0 diagnose, or research-engine CPU restart is authorized until PR #536 exact final head receives NO_BLOCKING_FINDING and the bounded recovery helper restores the three dependency-stopped controllers.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
