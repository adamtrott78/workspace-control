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

From Lambda, run exactly one source-bound rollback-failed controller recovery from detached exact checkout 9b402da8c0158be477ac00944b5c164ddef81193 using `sudo python3 scripts/lambda_ci_p1_restore_rollback_failed_controllers.py --expected-head 9b402da8c0158be477ac00944b5c164ddef81193`. The helper is authorized to issue only one `systemctl start` naming research-engine GPU, PADataset CPU, and PADataset GPU after proving exact failed/failed ExecMainStatus=1 NRestarts=0 target states, healthy shared services, no active project execution, and exact research-engine CPU preservation. Return the complete recovery output/receipt before any bootstrap retry, L0 diagnose, reconciliation, workspace-control activation, or research-engine CPU restart.

## Remaining work

- Run the independently reviewed rollback-failed controller recovery helper exactly once from merge 9b402da8c0158be477ac00944b5c164ddef81193 and inspect the complete receipt. It may start exactly research-engine GPU, PADataset CPU, and PADataset GPU; research-engine CPU must remain unchanged.
- Only after recovery PASS, retry the rollback-safe P1 bootstrap from the exact reviewed merge SHA and inspect the complete bootstrap output/receipt before any later gate.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- PR #539 is independently accepted and merged as 9b402da8c0158be477ac00944b5c164ddef81193, but Lambda remains in the post-incident state: research-engine GPU, PADataset CPU, and PADataset GPU are failed/failed with ExecMainStatus=1 and NRestarts=0; research-engine CPU remains intentionally quiesced at inactive/dead, ExecMainStatus=1, NRestarts=12411.
- The next live gate is exactly one source-bound run of scripts/lambda_ci_p1_restore_rollback_failed_controllers.py from detached exact checkout 9b402da8c0158be477ac00944b5c164ddef81193 with --expected-head set to the same SHA. Full recovery receipt must be inspected before any bootstrap retry.
- workspace-control activation remains separately blocked until recovery PASS, corrected bootstrap PASS, and a real GitHub -> L0 maintenance DIAGNOSE_LANE command produces a durable accepted receipt.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
