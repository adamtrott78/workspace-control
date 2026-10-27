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
- Remote branch: gitrunner-p1-quiesce-restart-storm
- Remote checkpoint: b7e69b960703712e758bed4ecbfd6dddc0ad445c
- Remote verified: false

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Validate and independently review the bounded pre-bootstrap research-engine CPU restart-storm quiesce helper. The helper must be source-head bound, prove no active research-engine execution, require provisioner/reconciler/reconcile-controller plus research-engine GPU and both PADataset controllers active, prove the target service uses Restart=on-failure and has NRestarts >=12110 increasing across two six-second observation intervals, and immediately before mutation recheck non-target services/execution absence. Its sole live mutation may be systemctl stop workspace-ci-controller@research-engine-cpu.service. It must then prove the target remains exactly stable inactive/dead for six seconds. It must never restart/start/enable a unit, install files, change policy, reconcile, or activate workspace-control. If independently accepted, run it once from the exact reviewed merge, inspect its receipt, then run the already-reviewed P1 bootstrap merge 6bd20890e2bc8a44dba8a33227cbb69b3e1368fd unchanged.

## Remaining work

- Validate and independently review PR #530, then retry the rollback-safe P1 bootstrap installer only from the exact reviewed merge SHA; preserve the three healthy controllers and keep workspace-control dormant.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- Fourth live bootstrap retry from reviewed merge 6bd20890e2bc8a44dba8a33227cbb69b3e1368fd aborted safely before mutation because research-engine CPU was in activating/auto-restart with ExecMainStatus=1 and NRestarts=12110. This confirms the pre-existing restart storm remains active and shared controller binary/template replacement cannot safely occur while that unit can relaunch mid-install.
- A bounded pre-bootstrap quiesce helper is implemented on gitrunner-p1-quiesce-restart-storm. It may stop exactly workspace-ci-controller@research-engine-cpu.service only after proving no local research execution, all non-target control services active, and NRestarts increasing across two observation intervals. It must then prove exact stable inactive/dead state. This helper requires exact-head validation and fresh independent review before any live use.
- The independently reviewed bootstrap merge 6bd20890e2bc8a44dba8a33227cbb69b3e1368fd remains unchanged and is the intended bootstrap executable after successful quiesce.
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
