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
- Remote checkpoint: a3f660806cfd8caa243fe9dfb4e3c25b2d451ac7
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement PRODUCTION_SCHEDULER_CANDIDATE_TRANSPORT_V1. Compose a scheduler application service around durable PostgreSQL state and ExecutorDispatchCoordinator: select only claimable READY/READY_TO_RESUME work, route by typed ExecutionRequirement/ExecutorProfile properties, emit deterministic effects or persistent-Instant OperatorActions, and stop/release on WAITING_EXTERNAL/WAITING_DEPENDENCIES without model polling. Replace the underspecified github-candidate target with an explicit candidate-only repository/ref/path contract; ingestion must read exact immutable commit bytes, bind commit SHA + content SHA, and invoke WorkerResultIntakeService idempotently. Prove restart/duplicate/stale/session-replacement behavior in repository CI. Do not activate live Tailscale Serve, real ChatGPT account interaction, or any new root route until Workspace Shell trusted authority is present.

## Remaining work

- Implement a production scheduler service over RuntimeCoordinator + ExecutorDispatchCoordinator so ready work is routed from durable typed state instead of test-only direct method calls; external/dependency waits must remain event-driven and consume no reasoning quanta.
- Freeze the GitHub candidate namespace contract with explicit repository/ref/path identity. Candidate writers may create proposal evidence only and must not mutate task capsules, authority policy, runtime control state, or authoritative branches.
- Implement exact candidate-source ingestion that binds immutable 40-char commit SHA + exact bytes before WorkerResultIntakeService and is idempotent across scheduler restart.
- Prove scheduler + candidate intake across PostgreSQL adapter recreation, stale candidate delivery, duplicate delivery, and persistent Instant session replacement.
- Re-check Workspace Shell trusted authority for the semantic live-host task only after repository production scheduler/candidate transport is validated; do not activate Tailscale/browser/account transport while TASK_NOT_FOUND persists.
- Finish remaining Operator Bridge Stage-10 trials and Stage-12 real-account calibration after the reviewed live route is authorized.
- Advance subscription Codex only after PR #627 lineage authority clears.
- Run live Research Engine proving workflow, mixed-executor fault injection, allowance/economics comparison, soak/resource tests, and PROD-03 readiness review.

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
