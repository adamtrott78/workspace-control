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
- Remote checkpoint: e1a91804f6cb5b1cdcd6b24c5bd454dae5790e2e
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement DURABLE_WORKER_RESULT_PUBLICATION_AND_INTAKE_V1. Manual Instant dispatch must atomically claim/start the target ReasoningProcess using a deterministic operator worker/lease identity before packet/session/action publication. Add a strict WorkerResultPublication contract bound to immutable source bytes plus exact action_generation/process_generation/session_generation/packet_sha256. Result intake may propose RESULT, TOO_LARGE, INTRINSICALLY_DIFFICULT, or WAIT_EXTERNAL only; it cannot grant authority. On valid durable publication, atomically acknowledge the session + OperatorAction and apply the corresponding process transition. RESULT must become TERMINAL_CANDIDATE and complete only after an independent validator. Exact duplicate publications must be idempotent; stale/mismatched/unknown-field publications fail closed. Prove schema-v6 compatibility and PostgreSQL adapter-restart intake. Do not scrape ChatGPT or activate live Tailscale transport.

## Remaining work

- Implement and validate durable worker-result publication/intake with exact action/process/session/packet generation fencing and no consumer-UI scraping.
- Make manual Instant dispatch own the ReasoningProcess lease atomically with packet/session/action planning so another executor cannot race the same leaf.
- Drive RESULT -> terminal candidate -> independent validator -> COMPLETED/repair-ready; TOO_LARGE -> recursive decomposition; INTRINSICALLY_DIFFICULT -> stronger-tier resume; WAIT_EXTERNAL -> event-driven wait.
- Add strict worker-result JSON codec/schema and future immutable GitHub candidate/intake adapter; worker output must never mutate authoritative task state directly or grant authority.
- After a reviewed default-branch activation route exists, run exact-host Tailscale fake-worker transport preflight and close INST-01.
- Finish remaining Operator Bridge Stage-10 gates and Stage-12 real-account calibration.
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
