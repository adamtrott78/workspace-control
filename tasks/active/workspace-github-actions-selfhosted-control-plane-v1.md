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

Fresh independent exact-head review of PR #558 only. Verify the exact candidate->ACTIVE policy delta and updated activation-state regressions; confirm no P2/P3/capacity/trigger widening; confirm the currently live reconciler from merge e4c81ac5fba8c4d9df8450b003147f90d771158b with installed SHA256 5e3c56c84f8e9755334ca4f0db7bdd7036f70b3e4cd404ebb02e8aa6b97185a9 will derive restart authority only for workspace-ci-controller@workspace-control-cpu.service if the documented live candidate baseline remains unchanged, while preserving research-engine CPU/GPU and PADataset CPU/GPU exact snapshots and honoring durable daemon-reload semantics. Review the proposed post-acceptance sequence: merge PR #558 with expected-head guard; require the resulting main Lambda CI Project Reconcile workflow run to succeed; before submission live-re-attest root reconciler digest/health, frozen automatic reconcile-controller, workspace-control CPU disabled/inactive, candidate installed policy, no active workspace-control execution units, and sibling snapshots; submit exactly one reconciliation-controller --once transaction from the reviewed main policy; capture the complete root receipt; require ACTIVE installed registry/manifest/route, workspace-control CPU active/running/enabled, restart set exactly workspace-control CPU, preserved sibling snapshots exact, daemon_reload_required/completed coherent, and no automatic workload trigger. Review whether the proposed one-shot submission and emergency-stop/rollback authority are sufficiently bounded; return NO_BLOCKING_FINDING only if the complete activation boundary is acceptable. Do not merge or mutate Lambda during review.

## Remaining work

- Obtain fresh independent exact-head review of PR #545, focused on source provenance, exact old installed digest binding, preservation of failed receipt/cursor, candidate dormancy, project-controller preservation, the single root-maintenance service restart mutation, bounded socket readiness, and rollback restoration.
- After accepted merge, run the reviewed installer exactly once from its exact merge SHA and inspect the complete hotfix receipt before any maintenance retry.
- Only after installer PASS, post exactly one new owner `/workspace-ci-maintain diagnose workspace-control cpu` command and prove a durable COMPLETED observation-only receipt; do not reuse failed comment 6437389584.
- Only after the diagnostic receipt is accepted may workspace-control activation be independently gated as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- PR #558 is review-only and must not be merged until fresh independent activation-boundary review returns NO_BLOCKING_FINDING.
- workspace-control remains live MIGRATION_CANDIDATE_NOT_INSTALLED / PLANNED_NOT_BOUND and workspace-ci-controller@workspace-control-cpu.service remains disabled/inactive until a reviewed main policy merge and one bounded reconciliation transaction occur.
- Do not start the automatic workspace-ci-reconcile-controller.service, issue APPLY/reconcile, start/enable workspace-control CPU manually, issue maintenance commands, restart/reset preserved sibling controllers, restart research-engine CPU, or widen P2/P3/capacity before activation review.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
