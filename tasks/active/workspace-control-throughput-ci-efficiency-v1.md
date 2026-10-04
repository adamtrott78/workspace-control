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
- Remote checkpoint: 28d1c892af9c015010e0700154cedd27aad21bac
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 7a26e648ec409c96a3f9b7c8620f566658700894
- Remote verified: true

## Next safe action

Start from https://github.com/adamtrott78/workspace-control and the normal root route. Resume on branch throughput-ci-efficiency-v1 at implementation checkpoint 28d1c892af9c015010e0700154cedd27aad21bac. Read architecture/throughput-ci-efficiency-v1.md and procedures/validation_routing.md. Do not mutate research-engine. The next gate is FULL_INTEGRATION validation of the workspace-control implementation: run the complete workspace-control unit/task-contract regression suite in a suitable runtime, inspect any failures, and repair on the isolated branch in one bounded mutation batch. Only after that passes should the representative before/after benchmark and PR/merge decision proceed.

## Remaining work

- Run the full workspace-control unit/task-contract regression suite against implementation checkpoint 28d1c892af9c015010e0700154cedd27aad21bac in a suitable runtime; do not merge before it passes.
- After full validation, open/review the workspace-control PR and benchmark representative FAST_STATIC, TARGETED_PR, and FULL_INTEGRATION control cycles.
- Record before/after mutation-call count, commit count, PR CI latency/restarts, selected validation tier, synchronous post-merge wait, and preserved provenance/checkpoint invariants.
- Only if benchmark evidence justifies repository-specific CI changes, explicitly expand research-engine mutation authority in this capsule before touching research-engine.

## Blockers / gates

- No external-practice research or risk-tier design has been completed yet; do not modify CI merely from intuition.
- The current task does not yet prove which canonical-main validations may safely become asynchronous or scheduled.
- Research-engine is read-only during the initial task stages; any representative CI mutation there requires explicit capsule authority expansion after design review.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-control-throughput-ci-efficiency-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
