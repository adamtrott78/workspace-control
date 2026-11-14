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
- Remote checkpoint: cf7a2393cc57c55e8bfb317afdf99d3fa89cd175
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement the fault/resource acceptance suite under tests/test_workspace_semantic_execution_backend_faults.py and extend .github/workflows/semantic-execution-validation.yml to run backend kernel/runtime/read-only/research-engine-shadow/fault tests explicitly. Cover crash after claim, crash after effect before checkpoint, duplicate/delayed/out-of-order event behavior, stale-generation fencing, executor/session disappearance, validator failure/timeout semantics, durable restart/reconciliation, and control-plane GPU blindness/resource-budget checks. Do not add write authority. After the suite is green, produce Architecture Review v0.3 from measured evidence.

## Remaining work

- Run explicit fault-injection acceptance for death after claim, death after effect before checkpoint, duplicate/delayed/out-of-order events, stale generations, executor/session loss, validator timeout, and durable recovery.
- Add semantic-execution-specific CI coverage for read-only/canary/fault tests plus resource gates.
- Measure/control-plane CPU/RSS/GPU-blindness targets and record evidence.
- Perform Architecture Review v0.3 from real implementation/canary/fault evidence and choose/retain/revise DBOS+PostgreSQL provisionally.
- Define the next bounded write-capable slice only if v0.3 evidence supports it.

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
