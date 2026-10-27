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
- Remote checkpoint: 74d565c4e6ce4954157c46e3289c952b4a1da7fd
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Operator: perform one read-only post-rollback incident fingerprint on Lambda. Capture exact service state/timestamps for provisioner, reconciler, reconcile-controller, research-engine CPU/GPU, PADataset CPU/GPU, and maintenance services; capture recent journal for research-engine GPU; capture ci-maintenance/workspace-ci-maintenance identity/group metadata; capture existence/hash metadata for bootstrap-touched files and maintenance state paths. Do not start/restart/stop/enable/disable any unit, do not reconcile, do not rerun bootstrap, and do not mutate files. Return the complete diagnostic output. Owner then determines whether rollback restored files/state, why research-engine GPU exited cleanly, and freezes the minimum independently reviewed recovery/correction.

## Remaining work

- Validate and independently review PR #530, then retry the rollback-safe P1 bootstrap installer only from the exact reviewed merge SHA; preserve the three healthy controllers and keep workspace-control dormant.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- Live bootstrap from reviewed merge 74d565c4e6ce4954157c46e3289c952b4a1da7fd crossed into the mutation phase and failed on deterministic maintenance-identity validation: systemd-sysusers created ci-maintenance with workspace-ci-maintenance as supplementary membership, while the installer incorrectly required that group to be the account primary GID.
- Rollback restored its authorized targets but finished INCOMPLETE because final preserved-service verification found workspace-ci-controller@research-engine-gpu.service loaded/enabled but inactive/dead with ExecMainStatus=0 and NRestarts=0. Current live host state must be fingerprinted read-only before any repair or retry.
- No further bootstrap, service restart, reconciliation, workspace-control activation, L0 diagnose, or research-engine CPU restart is authorized until the post-rollback live fingerprint is captured and independently bounded recovery is defined.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
