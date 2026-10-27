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

Validate the bounded correction PR containing: (1) a finite fail-closed wait for the Type=simple maintenance root Unix socket, (2) deferred restoration of dependency-stopped non-CPU controllers until all L0 readiness/commissioning gates pass, (3) post-start controller stabilization before certification, and (4) a source-bound one-shot recovery helper restricted to the exact current three-controller failed/failed ExecMainStatus=1 NRestarts=0 incident state. Obtain a fresh independent exact-head NO_BLOCKING_FINDING before merge or any Lambda mutation. Do not recover, retry bootstrap, diagnose L0, reconcile, activate workspace-control, or restart research-engine CPU before that review.

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
- No live recovery or bootstrap retry is authorized until the bounded readiness/sequencing correction and exact-state recovery helper pass repository validation and fresh independent review.
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
