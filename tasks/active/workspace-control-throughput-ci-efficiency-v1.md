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
- Remote branch: main
- Remote checkpoint: 016a8827e7ed5e7d59ff86240f6f974d330f819c
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 7a26e648ec409c96a3f9b7c8620f566658700894
- Remote verified: true

## Next safe action

Start from https://github.com/adamtrott78/workspace-control and the normal root route. The risk-routed validation implementation is canonical on main@016a8827e7ed5e7d59ff86240f6f974d330f819c and its merged tree exactly equals the FULL_INTEGRATION-tested PR tree. The follow-up branch throughput-fast-static-benchmark-v1 is intentionally task-state-only. If that follow-up is not yet merged, require its PR run to select FAST_STATIC, pass changed-task capsule/handoff synchronization, and skip unit/full-integration work; then merge only with the exact expected head SHA and verify merged-tree identity. If it is already merged, use that run as the validated FAST_STATIC benchmark and continue collecting efficiency telemetry from the active research-engine task without overriding that task's durable next_safe_action. Do not mutate research-engine from this capsule; repository-specific CI/profile changes require explicit authority.

## Remaining work

- Use the follow-up branch throughput-fast-static-benchmark-v1, whose complete diff from merged main is limited to this task JSON and its derived Markdown handoff, as the representative FAST_STATIC benchmark.
- Require its PR validation run to select FAST_STATIC, pass changed-task validation/handoff synchronization, and skip unit-regression plus full-integration steps. Record wall-clock evidence.
- After the FAST_STATIC benchmark passes, merge the task-state-only follow-up with an exact expected head SHA and prove merged-tree identity.
- Collect field telemetry from the active research-engine task on logical changes versus commits, mutation-call batching, PR timing/restarts, CI step cost, status-read/poll frequency, tested-tree duplication, idle waits, context/routing rereads, provenance repetition, runtime setup, and artifact-transfer overhead.
- Benchmark TARGETED_PR opportunistically on a real test-only change when one naturally occurs; do not manufacture code churn solely for a timing sample.
- Research-engine-specific validation tiers or CI workflow changes require a reviewed research-engine profile and explicit mutation authority; shared orchestration improvements do not grant that authority.

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
