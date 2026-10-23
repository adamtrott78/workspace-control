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
- Remote checkpoint: b09df52942fc0b7b49ee7f82a6f8242df0924fba
- Remote verified: true

## Next safe action

Implement only implement_read_only_research_engine_adapter from research-engine checkpoint b09df52942fc0b7b49ee7f82a6f8242df0924fba. Add adapter code under prototypes/semantic_control_integration/** and tests under tests/semantic_control_integration/**. The adapter may call only claim_support, qualifiers_for_method, source_level_counts, and provenance_path. It must never mutate the store or call models, network, Lambda, or executors. Convert read results into deterministic SemanticObservationV1-compatible records with exact repository/store/query/fixture provenance; prove semantic-answer equivalence on the ephemeral five-work fixture and measure projection overhead separately from the frozen relational latency. Do not implement workspace-control or EXTRACT binding yet.

## Remaining work

- Implement the read-only research-engine current-store adapter and prove relational-answer vs semantic-answer equivalence plus provenance preservation.
- Implement the read-only workspace-control snapshot adapter and cross-task/capability/authority queries.
- Wait for and bind only a durable accepted EXTRACT output checkpoint before EXTRACT-specific integration.
- Run cross-system integration benchmark and issue READY_FOR_PRODUCTION_PROMOTION, REVISE, or REJECT.

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
