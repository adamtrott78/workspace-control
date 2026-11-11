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

Wait for Lambda CI Workspace Control Validation run #437 / 43072034606, job 130702172851, for exact reconciled head f51b4ee201529d8785e920458700affced52ffdf. No additional controller repair is authorized or required unless this new run exposes a controller-specific failure.

## Remaining work

- Observe exact validation outcome for PR #606 reconciliation head f51b4ee201529d8785e920458700affced52ffdf.
- Freeze a bounded v3 production refresh/revival design that installs only reviewed v3 controller material and revives only the exact #389 REST terminal record under scheduler proof.
- Validate and independently review that live transaction before any host mutation.
- Execute once; prove #389 receives a fresh request/runner identity and proceeds naturally.
- Record exact-head validation outcome for workspace-control 50395aad06ab719b8207d9e7d3d8270a6bb35030 and hand control back to workspace-shell-multirepo-research-v1.

## Blockers / gates

- Controller incident is closed; current gate is normal exact-head validation of PR #606 run #437, presently queued.
- Run #389 remains queued because its durable v3 ledger is falsely terminal after cross-job JIT capacity was assigned to older run #388.
- Retired v2 workspace-control controller/scale-set must remain untouched; current production validation is served by workspace-ci-v3-controller@workspace-control-control-small-v1.service.
- Live v3 deployment/ledger revival requires its own bounded, source-bound, independently reviewed transaction after code acceptance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
