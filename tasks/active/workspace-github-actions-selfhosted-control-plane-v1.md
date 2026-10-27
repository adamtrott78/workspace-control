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

From Lambda, perform exactly one corrected P1 bootstrap retry from a detached exact checkout of reviewed executable checkpoint 9b402da8c0158be477ac00944b5c164ddef81193 using `sudo python3 scripts/lambda_ci_p1_bootstrap_install.py --expected-head 9b402da8c0158be477ac00944b5c164ddef81193`. Before mutation, the installer must prove research-engine CPU exactly loaded+enabled+inactive/dead+ExecMainStatus=1+NRestarts=12411 and the three non-CPU controllers healthy active/running status 0 NRestarts 0. The corrected installer must wait for the maintenance socket readiness gate, defer non-CPU controller restoration until L0 commissioning gates pass, and keep workspace-control dormant. Return the complete bootstrap output/receipt before any GitHub -> L0 diagnose, reconciliation, workspace-control activation, or research-engine CPU restart.

## Remaining work

- Retry the corrected rollback-safe P1 bootstrap exactly once from reviewed merge 9b402da8c0158be477ac00944b5c164ddef81193; preserve the three healthy non-CPU controllers and keep research-engine CPU unchanged and workspace-control dormant.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- Live rollback-failed controller recovery from reviewed merge 9b402da8c0158be477ac00944b5c164ddef81193 succeeded. research-engine GPU, PADataset CPU, and PADataset GPU are active/running with ExecMainStatus=0 and NRestarts=0; research-engine CPU remains intentionally quiesced and unchanged at inactive/dead, ExecMainStatus=1, NRestarts=12411.
- The next gate is one corrected P1 bootstrap retry from exact reviewed executable checkpoint 9b402da8c0158be477ac00944b5c164ddef81193 with --expected-head set to the same SHA. Full bootstrap output/receipt must be inspected before any L0 diagnose or workspace-control activation.
- workspace-control activation remains separately blocked until corrected bootstrap PASS and a real GitHub -> L0 maintenance DIAGNOSE_LANE command produces a durable accepted receipt.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
