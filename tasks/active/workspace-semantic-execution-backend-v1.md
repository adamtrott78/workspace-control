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
- Remote checkpoint: 34028182aaf1dc56d40cc607f8561c2337e16bf8
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement RECURSIVE_TASK_TREE_CONTRACT_AND_FANIN_V1 under semantic-execution/** and tests/test_workspace_semantic_execution_backend*.py. Add typed durable process/work contract metadata sufficient to preserve objective, mandatory constraints, provenance/evidence refs, authority refs, validator contract and output schema across recursive decomposition. Define durable disposition semantics that distinguish TOO_LARGE (decompose again) from INTRINSICALLY_DIFFICULT (escalation required). Reuse DomainKernel/RuntimeCoordinator dependency waits and generation fencing; prove two-level decomposition, independent leaf completion, fan-in only after all children validate, recovery during dependency wait, and fail-closed attempts to drop inherited obligations. Do not add Research Engine writes or executor authority.

## Remaining work

- Implement and validate recursive task-tree/decomposition contract semantics with inherited constraints, provenance refs, authority refs and validator obligations.
- Add durable TOO_LARGE -> DECOMPOSE and INTRINSICALLY_DIFFICULT -> ESCALATION_REQUIRED classification without conflating the two.
- Prove multi-level fan-out/fan-in, generation fencing, recovery and independent leaf completion under the production RuntimeCoordinator.
- Implement production session-broker semantics and recovery tests after the recursive task tree is durable.
- Bind backend action/status transport to the independently owned Operator Bridge through its authorized child task.
- Integrate subscription Codex only after its runtime/auth child clears the PR #627 lineage gate.
- Run the first mixed-executor Research Engine research-iterate slice and real-workflow resource/fault measurements.
- Propose a separately authorized low-consequence write-capable slice only after read-only decomposition/mixed-executor evidence passes.

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
