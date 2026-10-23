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
- Remote checkpoint: 291ce566c8544628584b91312c4ae3e784ca533e
- Remote verified: true

## Next safe action

Implement only measure_relational_baseline from research-engine checkpoint 291ce566c8544628584b91312c4ae3e784ca533e. Add a benchmark runner under prototypes/semantic_control_integration/** and an integration test under tests/semantic_control_integration/** that initializes only CI's ephemeral RESEARCH_ENGINE_DATABASE_URL, loads the exact frozen five-work fixture, validates exact answers, performs the frozen 5 warmups + 50 measured calls for each of Q1-Q4 using time.perf_counter_ns, prints one machine-readable SEMANTIC_CONTROL_RELATIONAL_BASELINE_V1 JSON record, and makes no threshold/performance claim. Do not touch production DB, src/research_engine/**, workflow files, adapters, EXTRACT, policies, Lambda, or executors yet.

## Remaining work

- Measure the frozen four-query PostgresStore relational baseline on CI's ephemeral non-production PostgreSQL service and persist the result.
- Implement read-only research-engine and workspace-control adapters and prove answer/provenance equivalence.
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
