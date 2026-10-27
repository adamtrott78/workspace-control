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
- Remote branch: gitrunner-p1-implementation
- Remote checkpoint: ee4f174f1247ccd1f5123600cdd9978dd67dd0e1
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Implement the bounded P1 tranche from the independently accepted v0.2 design: (1) change admission-v2 controller behavior so TotalAssignedJobs is non-authoritative for execution and unreconstructable assignment divergence enters durable fail-closed quarantine with no new AcquireJobs/JIT/root provision; (2) add the finite independently installed L0 maintenance path with typed DIAGNOSE_LANE, RESTART_CONTROLLER, QUIESCE_LANE_FOR_RECOVERY, RESUME_LANE_AFTER_RESET and exact stale-scale-set reset orchestration/receipts as frozen; (3) add the NOT_INSTALLED owner-commanded workspace-control JIT CPU validation workflow/profile scaffolding without live activation. Keep maxRunners=1/concurrency=1 and preserve all isolation/transport-vs-execution/P2/P3/rollback boundaries. Run repository/adversarial validation, freeze exact implementation identities, then obtain independent implementation review before any Lambda/live runner activation.

## Remaining work

- Implement only the reviewed P1 tranche: admission-v2 assignment-divergence quarantine/recovery, bounded independently installed L0 maintenance path, and owner-commanded workspace-control JIT CPU validation pilot.
- Preserve maxRunners=1 and manifest concurrency=1; do not implement resource-aware concurrency or raise capacity.
- Add adversarial tests for incomplete JobAssigned restart recovery, quarantine/no-acquire behavior, exact stale-scale-set reset preconditions, replay/idempotency, typed maintenance verbs, derived targets, peer-UID/root validation, no arbitrary root command surface, and single-retry gating.
- Validate workspace-control filesystem isolation, CPU/RAM/runtime envelope, no-GPU guarantee, deterministic receipts, rollback, and independent bootstrap availability.
- Freeze the exact P1 implementation PR and obtain the separately required independent implementation review before any live workspace-control runner activation.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency, hosted/bootstrap fallback removal, and temporary transport cleanup unauthorized.

## Blockers / gates

- P1 live activation remains blocked until the exact implementation PR passes repository/adversarial tests and receives the required independent implementation review.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
