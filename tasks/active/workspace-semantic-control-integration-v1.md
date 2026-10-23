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
- Remote checkpoint: 8bf738f2c6722cda60f98190b58892e8e7979918
- Remote verified: true

## Next safe action

Implement the pre-EXTRACT cross-system integration benchmark under prototypes/semantic_control_integration/**, benchmarks/semantic_control_integration/**, and tests/semantic_control_integration/** from research-engine checkpoint 8bf738f2c6722cda60f98190b58892e8e7979918. Use CI's ephemeral Postgres to build the validated research-engine semantic manifest, build the pinned workspace-control semantic manifest, prove all four relational answer hashes equal semantic reconstruction hashes, rerun gpu-small ALLOW/generic gpu-heavy DENY authority gates with zero authorization escapes, test workspace blob drift and research answer drift fail closed, and report empirical relational plus semantic projection overhead with no retroactive threshold. The benchmark must emit PRE_EXTRACT_INTEGRATION_PASS or REVISE and must record EXTRACT_BINDING=BLOCKED_EVIDENCE; it must not issue READY_FOR_PRODUCTION_PROMOTION while the accepted EXTRACT output gate is unresolved.

## Remaining work

- Run and persist a pre-EXTRACT cross-system benchmark across the validated research-engine and workspace-control adapters, relational baseline, semantic overhead, authority/adversary gates, and failure isolation.
- When the owning EXTRACT task reaches a durable accepted architecture/output checkpoint, resume bind_accepted_extract_output with a versioned adapter only.
- Rerun the final cross-system benchmark including the accepted EXTRACT adapter.
- Issue READY_FOR_PRODUCTION_PROMOTION, REVISE, or REJECT and, if ready, create a separate production-promotion task.

## Blockers / gates

- EXTRACT-specific binding and final production-promotion verdict are blocked on a durable accepted output checkpoint from research-engine-local-extract-redesign-v1. Current proposition-alignment state is implementation-only.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-control-integration-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
