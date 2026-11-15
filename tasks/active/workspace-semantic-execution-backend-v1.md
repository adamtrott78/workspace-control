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
- Remote checkpoint: b5695e8c42c546d549742279a54e5668874fdacc
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement DURABLE_OPERATOR_PACKET_MATERIALIZATION_V1 under semantic-execution/** and dedicated backend tests. Persist typed packet compilation inputs and expected hash, never packet text. Add an atomic planner that binds the exact current ExecutorSession generation, registers the packet source, and enqueues the OperatorAction in one CAS transition. Add a DurableOperatorPacketMaterializer that reconstructs PacketCompilationInput from durable state, resolves the exact ExecutorProfile, recompiles, and fails closed unless process generation/executor/payload ref/hash all match. Prove exact retry idempotency, stale recovery fencing, serialization compatibility and PostgreSQL adapter-restart reconstruction. Do not activate live Tailscale transport yet.

## Remaining work

- Implement and validate durable typed SemanticPacketSource records plus production packet materialization with packet text absent from durable state.
- Atomically compose current session binding, typed packet source and queued OperatorAction in one state-store CAS boundary.
- Prove exact retry idempotency, stale process/session fencing, deterministic materialization and PostgreSQL restart reconstruction.
- After packet materialization passes, add a production backend server composition/entrypoint and run localhost transport preflight before any Tailscale Serve activation.
- Activate the reviewed outbound-only Tailscale Serve path only after exact-host preflight; then run one fake-worker production transport action before any real ChatGPT account.
- Finish remaining Operator Bridge Stage-10 trials and then bounded Stage-12 real-account calibration.
- Integrate subscription Codex only after its PR #627 lineage gate clears.
- Run the mixed-executor Research Engine research-iterate proving workflow and close remaining November REL/E2E gates.

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
