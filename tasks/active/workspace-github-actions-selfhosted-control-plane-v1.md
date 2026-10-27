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

Fresh chat: start from the authoritative task capsule and exact Git state, verify reviewed merge 4d98555a678050e611502de1b9b8c35b4cf9c5fa is still the pinned executable checkpoint and no intervening live mutation is recorded, then perform one P1 bootstrap retry from a detached exact checkout of that merge with --expected-head set to the same SHA. The corrected installer must preserve research-engine CPU exactly at loaded+enabled+inactive/dead+ExecMainStatus=1+NRestarts=12411; after any shared provisioner restart it may restore only research-engine GPU, PADataset CPU, and PADataset GPU if they match the reviewed clean dependency-stop predicate. Return the complete bootstrap output before any GitHub -> L0 diagnose, reconciliation, workspace-control activation, or research-engine CPU restart.

## Remaining work

- Validate and independently review PR #530, then retry the rollback-safe P1 bootstrap installer only from the exact reviewed merge SHA; preserve the three healthy controllers and keep workspace-control dormant.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- Live dependency-stop recovery from reviewed merge 4d98555a678050e611502de1b9b8c35b4cf9c5fa succeeded with DEPENDENCY_STOPPED_CONTROLLERS_RESTORED. research-engine GPU, PADataset CPU, and PADataset GPU are active/running with ExecMainStatus=0 and NRestarts=0; research-engine CPU remains intentionally quiesced and unchanged at inactive/dead, ExecMainStatus=1, NRestarts=12411.
- The next gate is one rollback-safe P1 bootstrap retry from exact reviewed merge 4d98555a678050e611502de1b9b8c35b4cf9c5fa using the corrected installer that handles supplementary maintenance group membership and shared-provisioner dependency stops. Full output must be inspected before any L0 diagnose or workspace-control activation.
- workspace-control activation remains separately blocked until bootstrap install passes and a real GitHub -> L0 maintenance DIAGNOSE_LANE command produces a durable accepted receipt.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Task ID: `workspace-github-actions-selfhosted-control-plane-v1`

Start from the normal workspace-control root route.
Treat the authoritative task capsule, synchronized handoff, exact durable Git/runtime state, and referenced evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
