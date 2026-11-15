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
- Remote checkpoint: d3f6e2837d36a59c0244b85db7de8679ad4dba1e
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement MIXED_EXECUTOR_RESEARCH_ITERATE_VERTICAL_SLICE_V1. Add a generic dispatch coordinator over route_executor: HUMAN_ASSISTED persistent Chat profiles must plan an OperatorAction/candidate contract through OperatorDispatchPlanner; DETERMINISTIC profiles must execute only through CoordinatedActionService with exact AuthorityDecision=ALLOW and independent postcondition validation; unsupported invocation modes fail closed. Then prove a research-iterate root over frozen research-engine@1031861c03b2af8cff5cf72939bbbc83a95e65a4 recursively decomposes into at least one deterministic exact-source child and one persistent-Instant child, waits for both validated completions, resumes root synthesis through Instant, and completes only after independent validation. No model-name scheduler branches, no live Tailscale activation, no Codex dependency, no research-engine mutation.

## Remaining work

- Implement a generic ExecutorDispatchCoordinator that routes the same ReasoningProcess to deterministic authorized execution or persistent Instant operator dispatch based only on typed ExecutionRequirement/ExecutorProfile properties.
- Build a Research Engine research-iterate vertical slice over the frozen exact source/canary: root Instant decomposition, deterministic exact-source child, Instant reasoning child, validated fan-in, and Instant synthesis.
- Prove every completed leaf/result is independently validated and that routing uses requirement/capability/scarcity rather than model-name branches.
- Inject one Instant session/process loss into the mixed workflow and recover from durable state for E2E-03.
- After a reviewed default-branch activation route exists, run exact-host Tailscale fake-worker transport preflight and close INST-01.
- Finish remaining Operator Bridge Stage-10 trials and Stage-12 real-account calibration.
- Advance subscription Codex only after PR #627 lineage authority clears.
- Run November integrated reliability/soak/economics acceptance and explicit PROD-03 readiness review.

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
