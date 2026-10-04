<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-control-throughput-ci-efficiency-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-control-throughput-ci-efficiency-v1
- Title: Workspace Control Throughput & CI Efficiency v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Measure and remove avoidable latency from ChatGPT/GitHub/workspace-control execution loops while preserving provenance, fail-closed mutation semantics, durable recovery, and implementation quality. Optimize both orchestration overhead and CI topology so routine low-risk changes do not pay the same synchronous validation cost as high-risk production changes, without weakening the full safety net.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: throughput-ci-efficiency-v1
- Remote checkpoint: 0c50ab9123d7b1cfa16d10925c09f74e0ba7d91a
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 7a26e648ec409c96a3f9b7c8620f566658700894
- Remote verified: true

## Next safe action

Start from https://github.com/adamtrott78/workspace-control and the normal root route. PR #50 carries the FULL_INTEGRATION-validated implementation checkpoint 0c50ab9123d7b1cfa16d10925c09f74e0ba7d91a. If PR #50 is not yet merged, inspect the latest synchronize run produced by this task-state-only coordination update: require selected tier FAST_STATIC, successful changed-task contract/handoff synchronization, and skipped unit/full-integration steps. Then reread current main and PR #50 base/head/mergeability and merge only with the exact expected head SHA. If PR #50 is already merged, treat merged main as canonical and collect efficiency telemetry from the active research-engine task without overriding its durable next_safe_action. Do not mutate research-engine from this capsule; any research-engine-specific profile or CI change requires explicit authority.

## Remaining work

- Use this task-state-only JSON/Markdown synchronization as the representative FAST_STATIC PR benchmark. Require the latest PR #50 run to select FAST_STATIC, pass changed-task validation/handoff sync, and skip unit/full-integration steps.
- If the FAST_STATIC benchmark passes, reread current main plus PR #50 base/head/mergeability and merge with an expected head SHA. Prove whether the merged main tree equals the tested synthetic merge tree.
- Collect field telemetry from the active research-engine task on mutation batching, PR timing/restarts, CI step cost, status-read frequency, tested-tree duplication, idle waits, and other workspace-control overhead. Treat this as observational evidence without replacing that task's next_safe_action.
- Benchmark TARGETED_PR opportunistically on a real test-only change when one naturally occurs; do not manufacture code churn solely to obtain a timing sample.
- Research-engine-specific validation tiers or CI workflow changes require a reviewed research-engine profile and explicit mutation authority; this capsule does not grant that authority.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-control-throughput-ci-efficiency-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
