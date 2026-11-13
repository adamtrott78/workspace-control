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
- Remote checkpoint: 752351d064f815e600dcdf19f2ba154f7234211f
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Research the current official DBOS Python/PostgreSQL integration API, then implement the narrowest provisional adapters behind DurableRuntimePort and StateStorePort without leaking DBOS/PostgreSQL types into domain/application code. Keep deterministic in-memory adapters as the reference. The spike must test restart/wait/idempotency semantics and document any mismatch; if current DBOS semantics make this awkward, record evidence and stop before forcing the architecture. Do not add real external effect authority in this stage.

## Remaining work

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
