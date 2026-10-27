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

Fresh independent review of PR #545 only. Review the exact immutable final PR head and validated code/test checkpoint 3a4c7a706c39d3023cea3056bc2d49f80c275e0f. Verify that the helper is executing-file source-bound, requires exact expected HEAD and tracked cleanliness, requires the exact prior installed maintenance-service SHA256 5730040e5fc1ef2666207accac97194812b35cde89b027ac24ce62b0740e51ec, binds the failed diagnose receipt/comment 6437389584 and cursor without deleting or replaying them, requires workspace-control to remain MIGRATION_CANDIDATE_NOT_INSTALLED / PLANNED_NOT_BOUND with no active execution, preserves research-engine CPU and the three healthy non-CPU controllers, mutates only the installed maintenance-service file and one `systemctl restart workspace-ci-maintenance.service`, waits boundedly for socket readiness, verifies the installed digest equals the reviewed source, and on failure restores exact prior bytes plus root-service readiness before failing closed. Return NO_BLOCKING_FINDING or exact actionable blockers. Do not merge or mutate Lambda during review.

## Remaining work

- Obtain fresh independent exact-head review of PR #545, focused on source provenance, exact old installed digest binding, preservation of failed receipt/cursor, candidate dormancy, project-controller preservation, the single root-maintenance service restart mutation, bounded socket readiness, and rollback restoration.
- After accepted merge, run the reviewed installer exactly once from its exact merge SHA and inspect the complete hotfix receipt before any maintenance retry.
- Only after installer PASS, post exactly one new owner `/workspace-ci-maintain diagnose workspace-control cpu` command and prove a durable COMPLETED observation-only receipt; do not reuse failed comment 6437389584.
- Only after the diagnostic receipt is accepted may workspace-control activation be independently gated as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- The DIAGNOSE_LANE correction from PR #544 is independently accepted and merged, but it is not yet installed on Lambda.
- PR #545 contains the bounded source-bound rollback-safe installer for that correction. It passed validation at checkpoint 3a4c7a706c39d3023cea3056bc2d49f80c275e0f but still requires fresh independent exact-head review before merge or live use.
- Do not rerun the original bootstrap installer: the commissioned maintenance cursor now exists by design, and the bootstrap path explicitly rejects a preexisting cursor.
- Do not issue a second maintenance command, reconcile, activate workspace-control, restart/reset project controllers, restart research-engine CPU, or widen P2/P3/capacity before the installer is independently accepted and its live receipt is reviewed.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
