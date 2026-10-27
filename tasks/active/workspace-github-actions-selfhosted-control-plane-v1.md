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
- Remote checkpoint: f4664e67c82e84922f54b3ed9ae45b677b039837
- Remote verified: false

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Validate the exact corrected PR #528 head. If SUCCESS, request fresh independent re-review consuming review 5662021244. Verify: research-engine CPU is re-attested as still unhealthy before mutation; rollback covers failures at both initial stop boundaries; rollback never restarts the three preserved controllers and reports incomplete rollback on restoration failure; commissioning requires exactly INITIALIZED_NO_COMMANDS_EXECUTED with no preexisting cursor; and success fails closed unless the automatic reconcile-controller remains stopped. Do not merge or execute the installer until NO_BLOCKING_FINDING is durably recorded.

## Remaining work

- Run the bounded read-only Lambda host preflight against merged workspace-control main 99972dd906bb16099645237d584d380beca88171; do not mutate host state during preflight.
- From that evidence, install only the exact reviewed P1 controller/provisioner/runtime/maintenance/systemd/policy artifacts while preserving current research-engine/PADataset service availability and an independently recoverable bootstrap/rollback path.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- PR #528 bootstrap installer received independent BLOCKING FINDINGS review 5662021244 at head 46d7eb5ea1ed8b43931958c518e21bf6180b02c1. All five findings have corrected code/tests on the current branch, but corrected-head validation and fresh independent re-review remain required before any Lambda mutation.
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
