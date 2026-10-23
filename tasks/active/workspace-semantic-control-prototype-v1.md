<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-semantic-control-prototype-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-semantic-control-prototype-v1
- Title: Semantic Control Plane Prototype v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Build and benchmark an additive, deterministic semantic-control prototype over frozen research-engine and workspace-control evidence that proves provenance-preserving semantic observations, cross-store semantic federation, contradiction/time handling, targeted evidence escalation, bounded ontology/schema context retrieval, shared semantic-twin queries, and fail-closed action-candidate/DecisionEvaluation semantics without changing production scientific truth, EXTRACT/VERIFY behavior, policy authority, or execution.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: ce4c211bf28efa84d3e6113984bef9356ddceeb4
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: b1f862914f289e1b5df644d2479df085369f530a
- Remote verified: true

## Next safe action

Implement only integrated_benchmark_and_verdict from research-engine checkpoint b1f862914f289e1b5df644d2479df085369f530a. Add a deterministic prototype benchmark runner/report under prototypes/semantic_control/** and benchmarks/semantic_control/** plus tests under tests/semantic_control/**. Evaluate frozen P1-P8 expected answers using the implemented adapters/twin/evidence/decision components; hard-fail on any authorization escape, provenance loss, contradiction/history collapse, nondeterministic rebuild, or projection-mutation failure. Record relational latency baseline as NOT_MEASURED_IN_PROTOTYPE_SCOPE and make no performance promotion claim. A correctness/safety PROMOTE_TO_INTEGRATION verdict may only recommend a separate integration task; do not change production code, DB schema, policies, EXTRACT/VERIFY, Lambda, or executor routing.

## Remaining work

- Run the frozen P1-P8 integrated benchmark across adapters, semantic twin, evidence/context layer, and decision bridge.
- Persist a benchmark report with hard-gate disposition and explicit latency-baseline status.
- Issue PROMOTE_TO_INTEGRATION, REVISE, or REJECT. Any promotion creates a separate integration task and does not change production.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-control-prototype-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
