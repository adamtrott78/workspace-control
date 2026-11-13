<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-semantic-execution-backend-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-semantic-execution-backend-v1
- Title: Workspace Semantic Execution Backend v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Implement the first production-grade modular-monolith backend for Workspace Semantic Execution: a pure executor-agnostic domain kernel, deterministic packet compilation, typed executor/resource routing, durable runtime/state ports, provisional DBOS+PostgreSQL adapters, exact CandidateAction-to-ActionSpec authority compilation, EffectReceipt/postcondition validation, event-driven waits, and a real Research Engine shadow canary—without replacing GitRunner, Research Engine, Operator Bridge, project-local truth, or existing authority owners.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-semantic-execution-migration-v1
- Remote checkpoint: 6b27e9c057c6ea33fdf532112711a11e10ff3723
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement the production pure-domain kernel under semantic-execution/ with no infrastructure imports. Mirror the validated parent state/authority/effect invariants, add reference-parity tests under tests/test_workspace_semantic_execution_backend*.py, and validate the exact head before beginning packet/compiler/router work. Do not add DBOS/PostgreSQL or external executor effects until the pure domain boundary is green.

## Remaining work

- Implement pure production domain types/state machine and prove reference parity.
- Implement deterministic packet compiler and executor/resource/session registry.
- Implement ports plus deterministic in-memory adapters/fake clock.
- Spike DBOS+PostgreSQL behind ports without freezing the substrate.
- Implement first read-only exact-effect executor plus receipt/postcondition validator.
- Run the real Research Engine shadow canary with zero source mutation.
- Run crash/fault/resource acceptance and Architecture Review v0.3.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-execution-backend-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
