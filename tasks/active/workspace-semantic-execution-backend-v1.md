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
- Remote checkpoint: 0afd7837f15ccc573d9dba8ce0422aa5a2d0b061
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Advance INTEGRATED_RELIABILITY_AND_LIVE_PROVING_PREPARATION without bypassing the suspended live-host authority gate. Add scheduler-level stale-generation/restart/duplicate-candidate/session-replacement fault coverage and a bounded no-GPU soak over durable PostgreSQL state. Prepare the exact live research-iterate proving fixture and rollback/provenance checklist. Separately re-check the Codex PR #627 lineage and Operator Bridge remaining Stage-10 gates under their owning tasks; do not mutate live semantic host/Tailscale state while Workspace Shell returns TASK_NOT_FOUND.

## Remaining work

- Run scheduler-level fault/soak campaign covering stale dispatch generation, duplicate immutable candidate delivery, scheduler restart, external wait no-poll behavior, and session replacement composition.
- Prepare exact live proving fixture and rollback/provenance checklist without activating any host route.
- Resume live Operator Bridge backend + Tailscale fake-worker proof only when Workspace Shell trusted authority contains the semantic task.
- Finish remaining Operator Bridge Stage-10 trials and bounded Stage-12 real-account calibration under its owning task.
- Resume Workspace Control subscription Codex child if/when PR #627 lineage authority clears.
- Run live mixed Research Engine proving workflow, allowance/economics comparison, soak/resource acceptance and final PROD-03 review.

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
