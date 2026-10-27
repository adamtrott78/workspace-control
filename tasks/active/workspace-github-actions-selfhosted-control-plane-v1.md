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

Fresh independent corrected-head re-review of PR #545 only. Verify BF-4 is closed by isolated MainPID-only forward and rollback regressions that hold InvocationID constant. Forward regression must prove a MainPID-only controller change rejects success with `maintenance controller MainPID changed during hotfix`, restores exact prior bytes, and uses the exact non-propagating root-service restart on forward and rollback. Rollback regression must prove a MainPID-only change with InvocationID unchanged prevents rollback certification and is reported as incomplete rollback. Regression-check BF-1 rc==0 dormancy inspection, BF-2 live AF_UNIX listener readiness, BF-3 ignore-dependencies restart plus InvocationID/MainPID preservation implementation, source binding, exact old digest, failed receipt/cursor preservation, workspace-control dormancy, research CPU/non-CPU controller preservation, PR #544 DIAGNOSE-only observation boundary, and no activation/reconciliation/P2-P3/capacity widening. Return NO_BLOCKING_FINDING or exact actionable blockers. Do not merge or mutate Lambda during review.

## Remaining work

- Obtain fresh independent exact-head review of PR #545, focused on source provenance, exact old installed digest binding, preservation of failed receipt/cursor, candidate dormancy, project-controller preservation, the single root-maintenance service restart mutation, bounded socket readiness, and rollback restoration.
- After accepted merge, run the reviewed installer exactly once from its exact merge SHA and inspect the complete hotfix receipt before any maintenance retry.
- Only after installer PASS, post exactly one new owner `/workspace-ci-maintain diagnose workspace-control cpu` command and prove a durable COMPLETED observation-only receipt; do not reuse failed comment 6437389584.
- Only after the diagnostic receipt is accepted may workspace-control activation be independently gated as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- PR #544 DIAGNOSE_LANE correction is independently accepted and merged but not yet installed on Lambda.
- PR #545 head a22cbc4378b4a5aa8fd1125e8e9cecb6127c746c was independently rejected by comment 6438420782 for BF-4 missing isolated MainPID-only forward/rollback regressions.
- BF-4 is corrected and validated at checkpoint 889da37c13a82d74c7ad65f17a4b161178f37e82; fresh independent corrected-head review remains required before merge/live use.
- Do not issue another maintenance command, reconcile, activate workspace-control, restart/reset project controllers, restart research-engine CPU, or widen P2/P3/capacity before corrected-head NO_BLOCKING_FINDING and reviewed live hotfix receipt.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
