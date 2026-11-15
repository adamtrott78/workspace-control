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
- Remote checkpoint: 6979165961cc848ca8b37acd58f7c91e7a48df65
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement OPERATOR_ACTION_STORE_AND_TRANSPORT_CONTRACT_V1. Add durable OperatorAction records/lifecycle to semantic-execution control state, with deterministic queue priority/sequence, exact action/process/slot/session-generation identity, atomic claim, revalidation before local preparation, local failure/block/completion receipts, durable-ack transition, and Ready/SentUnconfirmed status projection. Bind action validity to current ExecutorSession and process generations; stale actions must fail closed. Freeze an outbound authenticated production transport contract for the Windows helper without Git polling, embedded GitHub credentials, helper inbound listeners, or authority creation. Do not mutate operator-bridge/** from the backend task.

## Remaining work

- Implement durable OperatorAction lifecycle/store + workload-status projection bound to current process/session generations.
- Freeze a bounded production OperatorBridge transport contract consistent with UX-12: helper-originated authenticated outbound connection, no embedded GitHub credential, no unauthenticated inbound helper listener, no page/content access.
- Hand the transport contract to workspace-operator-bridge-implementation-v1 and implement its production IOperatorActionPort adapter only under that task authority.
- Finish remaining Stage-10 Operator Bridge trials and then bounded Stage-12 real-account calibration.
- Integrate subscription Codex after its runtime/auth child clears the PR #627 lineage gate.
- Run the first mixed-executor Research Engine research-iterate slice and close remaining November REL/E2E gates.

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
