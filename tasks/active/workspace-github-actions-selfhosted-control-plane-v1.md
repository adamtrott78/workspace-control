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

Fresh independent exact-head review of PR #555 only. Consume BF-3 comment 6449758373, accepted PR #554 review 6449729967, and the authoritative task capsule. Verify the durable daemon-reload obligation: first-attempt transaction state must freeze whether target systemd controller drop-ins require daemon-reload; successful reload completion must be durably journaled before any pending restart; resume with required-but-uncompleted reload must execute daemon-reload before restart even when the drop-in bytes are already materialized; malformed/incompatible reload state must fail closed; if reload is marked complete, target drop-in drift must fail closed rather than be rewritten; and desired drop-in/environment bytes must be re-attested immediately before restart. Verify the interruption regression specifically fails at daemon-reload after drop-in materialization and proves retry order daemon-reload before workspace-control restart. Regression-check BF-1/BF-2 transaction/dormancy semantics and the accepted PR #554 successful-bootstrap live-baseline installer pin remain intact. Return NO_BLOCKING_FINDING or exact actionable blockers. Do not merge or mutate Lambda during review.

## Remaining work

- Obtain fresh independent exact-head review of PR #545, focused on source provenance, exact old installed digest binding, preservation of failed receipt/cursor, candidate dormancy, project-controller preservation, the single root-maintenance service restart mutation, bounded socket readiness, and rollback restoration.
- After accepted merge, run the reviewed installer exactly once from its exact merge SHA and inspect the complete hotfix receipt before any maintenance retry.
- Only after installer PASS, post exactly one new owner `/workspace-ci-maintain diagnose workspace-control cpu` command and prove a durable COMPLETED observation-only receipt; do not reuse failed comment 6437389584.
- Only after the diagnostic receipt is accepted may workspace-control activation be independently gated as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- P1 live reconciler-hotfix retry remains blocked pending fresh independent exact-head review of PR #555 BF-3 correction.
- The live Lambda reconciler still has the pre-fix reconciliation behavior because the first hotfix attempt failed before mutation; do not reconcile or activate workspace-control.
- Do not rerun the reconciler hotfix installer until PR #555 receives NO_BLOCKING_FINDING and is merged.
- Do not issue maintenance commands, restart/reset project controllers, restart research-engine CPU, or widen P2/P3/capacity.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
