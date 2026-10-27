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
- Remote checkpoint: 4d98555a678050e611502de1b9b8c35b4cf9c5fa
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Operator: execute scripts/lambda_ci_p1_restore_dependency_stopped_controllers.py from a detached exact checkout of reviewed merge 4d98555a678050e611502de1b9b8c35b4cf9c5fa with --expected-head set to that exact SHA and capture full output. The helper must fail closed unless shared provisioner/reconciler/reconcile-controller are active/running, no research-engine/PADataset execution units are active, research-engine CPU exactly remains loaded+enabled+inactive/dead+ExecMainStatus=1+NRestarts=12411, and research-engine GPU/PADataset CPU/PADataset GPU are each loaded+enabled+inactive/dead+ExecMainStatus=0+NRestarts=0. Sole authorized mutation is one systemctl start command containing exactly those three non-CPU controller units. Return the complete P1_DEPENDENCY_STOPPED_CONTROLLER_RECOVERY_RECEIPT before any bootstrap retry.

## Remaining work

- Validate and independently review PR #530, then retry the rollback-safe P1 bootstrap installer only from the exact reviewed merge SHA; preserve the three healthy controllers and keep workspace-control dormant.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- PR #536 corrected post-rollback recovery and bootstrap dependency-stop handling is independently accepted and merged as workspace-control@4d98555a678050e611502de1b9b8c35b4cf9c5fa. The next gate is one operator-executed incident recovery helper run from that exact reviewed merge SHA.
- The recovery helper may start only research-engine GPU, PADataset CPU, and PADataset GPU if and only if the live host still exactly matches the captured incident state. Research-engine CPU must remain unchanged at inactive/dead, ExecMainStatus=1, NRestarts=12411.
- No bootstrap retry, workspace-control activation, reconciliation, L0 diagnose, or research-engine CPU restart is authorized until the recovery receipt is inspected and accepted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
