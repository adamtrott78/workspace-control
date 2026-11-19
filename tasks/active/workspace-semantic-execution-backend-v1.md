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
- Remote checkpoint: 41d320100a0c2ee3890c900ed5295a94b08213af
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

BACKEND IS REPOSITORY-COMPLETE FOR THE CURRENT CRITICAL PATH. Preserve validated scheduler/recovery state. Do not add speculative backend features or reactivate live transport via generic shell. Resume only when an exact reviewed/default-branch Workspace Shell authority route exists for the semantic task; then launch the validated localhost Operator Bridge server, bind reviewed private Tailscale Serve, prove one fake-worker round trip, and run the live mixed Research Engine research-iterate fault/provenance/resource fixture. Meanwhile allow Operator Bridge and Reasoning Economy child tasks to advance independently.

## Remaining work

- Wait for exact reviewed/default-branch Workspace Shell authority for semantic live-host activation; do not bypass TASK_NOT_FOUND.
- When authority exists: launch validated localhost backend + reviewed Tailscale Serve and prove fake-worker action/status/result round trip before any real account.
- Run the live mixed Research Engine research-iterate workflow with one forced Instant session/process loss and no manual state reconstruction.
- Capture live resource/soak/provenance/rollback evidence and feed calibrated economics into the November acceptance matrix.
- Participate in final PROD-03 PROMOTE_V0/HOLD/REVISE review.

## Blockers / gates

- LIVE OPERATOR TRANSPORT AUTHORITY: production server/client code is validated, but Workspace Shell trusted authority does not contain the semantic-execution backend/umbrella task IDs. Live backend-process and Tailscale Serve activation must wait for an exact reviewed/default-branch authority route; generic shell/sidecar bypass is forbidden.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-execution-backend-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
