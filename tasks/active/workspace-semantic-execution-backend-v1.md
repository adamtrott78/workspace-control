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
- Remote checkpoint: 6eb4744c5c01affc529257f29acb7c0bf6fff837
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

VALIDATE OPERATOR_BRIDGE_SERVER_COMPOSITION_AND_PRIVATE_PREFLIGHT_V1. The server must load the existing Postgres state key (never silently initialize a new control graph), use DurableOperatorPacketMaterializer + initial ExecutorRegistry, bind only 127.0.0.1, accept the fixed Tailscale-User-Login proxy identity header, and take DSN/expected identity only from environment with secret fields excluded from repr/log output. Dedicated integration must prove a Postgres-backed planned action is visible in status and claim returns the exact reconstructed packet. After repository validation, stop before live host mutation unless a reviewed activation path exists.

## Remaining work

- Validate the production Postgres-backed Operator Bridge server composition and localhost claim path.
- After exact server blob is validated, define reviewed activation authority for launching the backend process and Tailscale Serve without widening generic shell/root capability.
- Run exact-host Linux/Windows Tailscale preflight with content-free identity/reachability evidence; do not log the user login or DSN.
- Run one fake-worker action/status round trip through the real private transport and only then mark INST-01 PASS.
- Finish remaining Operator Bridge Stage-10 trials and bounded Stage-12 real-account calibration.
- Advance subscription Codex only after PR #627 lineage authority clears.
- Run mixed-executor Research Engine research-iterate and remaining November reliability/soak acceptance.

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
