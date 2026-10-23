<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-semantic-control-integration-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-semantic-control-integration-v1
- Title: Semantic Control Integration v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Integrate the validated semantic-control prototype with the real current research-engine and workspace-control authority/data boundaries through read-only, additive adapters and measurable benchmarks, while preserving existing authoritative stores, fail-closed policy semantics, and complete isolation from the still-evolving Local EXTRACT scientific architecture. Measure the missing relational/query baseline, prove cross-system adapter correctness, and bind future accepted EXTRACT outputs only through a versioned adapter before considering any production promotion.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 91459f5f6afa0d71394d63155c2fe8dfdc65a4b7
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 4febcf79bca2b40a0b48ddd66ac87c98ecf983d0
- Remote verified: true

## Next safe action

Implement only implement_workspace_control_snapshot_adapter from the frozen workspace-control source manifest. Add bounded snapshot inputs under benchmarks/semantic_control_integration/**, adapter code under prototypes/semantic_control_integration/**, and tests under tests/semantic_control_integration/**. Project root workload policy as NORMATIVE authority, project/profile/execution-contract and task dependency state as EXECUTION observations, and preserve exact Git blob provenance. Prove deterministic rebuild, workload capability+authority queries, explicit policy DENY precedence over capability/routes, stale/blob-drift fail-closed behavior, and Local EXTRACT dependency_state_only semantics. Do not bind accepted EXTRACT output yet and do not mutate workspace-control authority files.

## Remaining work

- Implement the read-only workspace-control snapshot adapter and cross-task/capability/authority queries.
- Wait for and bind only a durable accepted EXTRACT output checkpoint before EXTRACT-specific integration.
- Run cross-system integration benchmark on all currently authorized components and rerun authority/failure-isolation gates.
- After accepted EXTRACT binding exists, complete final integration benchmark and issue READY_FOR_PRODUCTION_PROMOTION, REVISE, or REJECT.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-control-integration-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
