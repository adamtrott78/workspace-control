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
- Remote checkpoint: f104361f3d27bf1a4548acf6f643eb454e847c9a
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement PERSISTENT_EXECUTOR_SESSION_BROKER_V1 under semantic-execution/** and tests/test_workspace_semantic_execution_backend*.py. Add a durable ExecutorSession/session-slot model separate from chat transcript correctness, with session_id, slot_id, executor_id, generation, lifecycle state, bound process/generation, context/rotation metadata and last durable acknowledgment. Reuse ExecutorProfile session/lifecycle/reset-policy semantics. Prove: healthy persistent sessions are reusable; stale session generations cannot publish current work; session loss/auth loss/context-threshold retirement advances generation and makes old acknowledgments stale; replacement sessions resume from deterministic packet/state rather than transcript; machine-stateless executors do not allocate persistent sessions; and no session state grants execution authority. Do not mutate operator-bridge/** from this backend task.

## Remaining work

- Implement and validate persistent ExecutorSession/session-slot semantics with generation fencing, explicit reuse/rotate/replace policy, loss recovery and stateless resume from durable typed state.
- Define the backend OperatorAction/status contract produced from eligible persistent-chat work without mutating the independently owned Operator Bridge implementation.
- Bind backend action/status transport to Operator Bridge only through workspace-operator-bridge-implementation-v1 authority.
- Integrate subscription Codex after its runtime/auth child clears the PR #627 lineage gate.
- Run the first mixed-executor Research Engine research-iterate slice using recursive decomposition plus deterministic/Instant/Codex routing.
- Run real-workflow fault/resource measurements and close remaining November ORCH/REL/E2E acceptance gates.
- Propose a separately authorized low-consequence write-capable slice only after read-only mixed-executor evidence passes.

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
