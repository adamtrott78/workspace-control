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
- Remote checkpoint: 99972dd906bb16099645237d584d380beca88171
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Perform a read-only preflight on the Lambda host from an exact clean checkout of merged workspace-control main 99972dd906bb16099645237d584d380beca88171. Verify current installed service states and restart counts; active workspace-ci transient units/processes; installed controller/provisioner/reconciler/runtime file identities; installed registry/project manifests; controller/reconciler/maintenance identities and token-file ownership/modes (without reading token contents); /run/workspace-ci socket ownership/modes; current workspace-control/PADataset/research-engine project roots and controller envs; and availability of the isolated Go 1.26.3 toolchain. Do not stop/restart/copy/install/enable/disable/reconcile/activate anything during this preflight. Use the evidence to derive the exact rollback-safe P1 host upgrade and activation commands.

## Remaining work

- Run the bounded read-only Lambda host preflight against merged workspace-control main 99972dd906bb16099645237d584d380beca88171; do not mutate host state during preflight.
- From that evidence, install only the exact reviewed P1 controller/provisioner/runtime/maintenance/systemd/policy artifacts while preserving current research-engine/PADataset service availability and an independently recoverable bootstrap/rollback path.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- P1 implementation review is satisfied. Live installation/activation now requires a read-only Lambda host preflight proving the current installed services, identities, credentials, source versions, active transient work, rollback-relevant state, and independent reconciliation/bootstrap path before any root mutation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
