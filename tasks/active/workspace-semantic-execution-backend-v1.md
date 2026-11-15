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
- Remote checkpoint: cef754dbd2484081b641c194f1dd0020d85dfc78
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement RESEARCH_ENGINE_COORDINATED_READ_ONLY_VERTICAL_SLICE_V1 under semantic-execution/** and tests/test_workspace_semantic_execution_backend*.py. Reuse the validated DomainKernel, RuntimeCoordinator, ExecutorRegistry, SemanticPacketCompiler, StaticAuthorityEvaluator, exact Research Engine repository read executor, and independent postcondition validator. The service must return structured routing/packet/authority/receipt/validation evidence and reach COMPLETED only after validator PASS. Add negative tests for unknown authority, stale generation, no eligible executor, changed-source validation failure, duplicate-effect safety, and deterministic packet hashing. Do not mutate research-engine and do not add write authority.

## Remaining work

- Implement and validate the coordinated Research Engine read-only vertical slice described by Architecture Review v0.3.
- Add production session-broker semantics and recovery tests after the coordinated slice proves router/packet/runtime composition.
- Bind the backend action/status transport to the independently owned Operator Bridge only through its authorized child task.
- Integrate subscription Codex as an executor only after its runtime/auth child clears the PR #627 lineage gate.
- Measure real-workflow control-plane CPU/RSS and repeat fault injection on the integrated slice.
- Propose a separately authorized low-consequence write-capable slice only after coordinated read-only evidence passes.

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
