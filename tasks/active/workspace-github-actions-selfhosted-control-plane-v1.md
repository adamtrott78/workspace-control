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
- Remote branch: gitrunner-p1-bootstrap-install
- Remote checkpoint: 58b8feda8684266d05111ce8b1bcbaecb39de4b9
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Validate the exact gitrunner-p1-bootstrap-install head. Review scripts/lambda_ci_p1_bootstrap_install.py as a one-shot root bootstrap bound to the 2026-10-27 read-only host fingerprint. It must freeze automatic reconciliation before policy installation, back up every touched file, install only reviewed P1 controller/runtime/reconciler/L0 artifacts, keep workspace-control MIGRATION_CANDIDATE_NOT_INSTALLED / PLANNED_NOT_BOUND, restart only the shared provisioner/reconciler and the already-unhealthy research-engine CPU controller, preserve the three healthy project/lane controllers, initialize maintenance issue #527 without executing historical commands, retain rollback, and leave the automatic reconcile controller stopped on success. If exact-head validation passes, obtain fresh independent review before any host mutation.

## Remaining work

- Run the bounded read-only Lambda host preflight against merged workspace-control main 99972dd906bb16099645237d584d380beca88171; do not mutate host state during preflight.
- From that evidence, install only the exact reviewed P1 controller/provisioner/runtime/maintenance/systemd/policy artifacts while preserving current research-engine/PADataset service availability and an independently recoverable bootstrap/rollback path.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- P1 live bootstrap installer is implemented but unexecuted. Because it performs privileged host mutation, exact-head repository validation and a fresh independent bootstrap-install review are required before the operator runs it.
- workspace-control activation remains separately blocked until the bootstrap install passes and a real GitHub -> L0 maintenance DIAGNOSE_LANE command produces a durable accepted receipt.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
