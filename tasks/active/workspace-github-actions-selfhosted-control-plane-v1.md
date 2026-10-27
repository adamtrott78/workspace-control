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

Fresh independent review of PR #539 only. Review the final immutable PR head and the validated code/test checkpoint 70b413fc2cfe63226ead00804eba8ea6ef969c8e. Verify the Type=simple maintenance socket readiness wait is finite/fail-closed; non-CPU controller restoration is deferred until all L0 commissioning gates pass; post-start stabilization cannot widen controller authority; and the source-bound rollback-failed recovery helper accepts only the exact three-controller failed/failed ExecMainStatus=1 NRestarts=0 incident state while preserving research-engine CPU and healthy shared services. Return NO_BLOCKING_FINDING or exact actionable blockers. Do not merge or mutate Lambda before that disposition.

## Remaining work

- Validate the bounded maintenance-socket readiness / deferred-controller-restoration correction and exact-state rollback-failed recovery helper on a dedicated PR; obtain fresh independent exact-head review before merge or Lambda mutation.
- After reviewed merge, run only the source-bound rollback-failed controller recovery helper from an exact detached checkout of that merge and inspect the complete receipt. It may start exactly research-engine GPU, PADataset CPU, and PADataset GPU; research-engine CPU must remain unchanged.
- Only after recovery PASS, retry the rollback-safe P1 bootstrap from the exact reviewed merge SHA and inspect the complete bootstrap output/receipt before any later gate.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- The live P1 bootstrap incident is understood but not yet repaired on Lambda. The accepted root causes are (1) an immediate Unix-socket readiness check against a Type=simple maintenance daemon and (2) restoring project controllers before later L0 gates, allowing rollback to stop freshly initializing controllers.
- research-engine GPU, PADataset CPU, and PADataset GPU remain in the exact rollback-canceled failed/failed state with ExecMainStatus=1 and NRestarts=0. research-engine CPU remains intentionally quiesced at inactive/dead, ExecMainStatus=1, NRestarts=12411.
- PR #539 code/test checkpoint 70b413fc2cfe63226ead00804eba8ea6ef969c8e passed Workspace Control Validation run #940. Fresh independent review of the final PR head remains the sole gate before merge/live recovery.
- workspace-control activation remains separately blocked until a corrected bootstrap install passes and a real GitHub -> L0 maintenance DIAGNOSE_LANE command produces a durable accepted receipt.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
