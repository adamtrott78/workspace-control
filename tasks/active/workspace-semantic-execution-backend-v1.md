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
- Remote checkpoint: e9a1f976370ce5b91a2c0785ab4413d68667cc8e
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement INSTANT_CANDIDATE_PUBLICATION_CONTRACT_AND_E2E_V1. Extend deterministic packet compilation with a typed publication contract supplied by the dispatch planner: exact publication_id/action_id/action_generation/process_generation/worker_slot_id/session_generation, worker-result schema ref, and a candidate-only target ref. Do not embed packet_sha256 inside the canonical payload (the worker must copy the packet_sha256 header into its publication) to avoid self-reference. The target must be proposal-only and must explicitly forbid task-capsule/authority mutation. Add an exact-source candidate adapter that parses immutable bytes with source_ref/source_sha256 and invokes WorkerResultIntakeService. Prove the complete fake-worker loop through the production HTTP claim/local-prepared boundary and PostgreSQL restart. Do not activate live Tailscale transport or real ChatGPT account yet.

## Remaining work

- Embed a typed non-authoritative result-publication contract in Instant packets, including exact action/process/session generations and schema/candidate target while avoiding self-referential packet hashing.
- Implement a candidate-source adapter that binds immutable result bytes/source SHA and feeds WorkerResultIntakeService; candidate publication must not mutate authoritative task state or authority fields.
- Prove one full fake-worker Instant loop: atomic dispatch -> production HTTP claim -> local prepared -> immutable candidate result -> exact-source parse -> durable intake -> independent validation -> process/action/session completion.
- Repeat the full loop across PostgreSQL adapter recreation and stale candidate/recovery faults.
- After a reviewed default-branch activation route exists, run exact-host Tailscale fake-worker transport preflight and close INST-01.
- Finish remaining Operator Bridge Stage-10 trials and Stage-12 real-account calibration.
- Advance subscription Codex only after PR #627 lineage authority clears.
- Run mixed-executor Research Engine research-iterate and remaining November reliability/soak acceptance.

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
