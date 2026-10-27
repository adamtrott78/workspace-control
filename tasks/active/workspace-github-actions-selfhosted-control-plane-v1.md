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

Validate and independently review the bounded preactivation diagnose correction on branch/PR `p1-preactivation-diagnose-fix`. Review must verify that only DIAGNOSE_LANE can set `allow_migration_candidate_observation`, that it accepts only exact registry+manifest `MIGRATION_CANDIDATE_NOT_INSTALLED`, that mixed/other inactive states fail closed, that all mutating maintenance verbs remain ACTIVE-only, and that the diagnose path performs no systemctl mutation. Do not merge or mutate Lambda before exact-head NO_BLOCKING_FINDING.

## Remaining work

- Validate the observation-only preactivation diagnose correction and adversarial tests on a dedicated PR; obtain fresh independent exact-head review before merge or Lambda mutation.
- After reviewed merge, install only the corrected root maintenance service through the already-reviewed/bootstrap authority or an equally bounded reviewed install path, without activating workspace-control.
- Then post exactly one new owner diagnose command and prove a durable COMPLETED receipt for DIAGNOSE_LANE on the migration candidate; do not reuse comment 6437389584.
- Only after a real GitHub -> L0 diagnostic receipt is durably accepted may workspace-control activation be independently gated as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- The first live GitHub -> L0 diagnose command failed closed as designed by the current code because workspace-control is a pre-activation migration candidate. That failure is durably evidenced by comment 6437389584 and its FAILED_CLOSED receipt.
- A bounded correction is now under review: allow observation-only DIAGNOSE_LANE for exact MIGRATION_CANDIDATE_NOT_INSTALLED registry+manifest state while preserving ACTIVE-only requirements for every mutating maintenance operation.
- Do not issue a second maintenance command, modify Lambda, reconcile, activate workspace-control, restart/reset controllers, restart research-engine CPU, or widen P2/P3/capacity until the correction passes validation and fresh independent exact-head review.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
