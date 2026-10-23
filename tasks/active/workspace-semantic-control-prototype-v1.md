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
- Remote checkpoint: 007d88b37f34554e8be8e8ad9c976e3724a82521
- Remote verified: true

## Next safe action

Implement only build_semantic_twin_and_query_layer from research-engine checkpoint 007d88b37f34554e8be8e8ad9c976e3724a82521. Add in-memory deterministic projection/query code under prototypes/semantic_control/** and tests under tests/semantic_control/**. Prove provenance traversal, contradiction preservation, temporal/supersession replay, deterministic rebuild, and the frozen P6 multi-hop task/scientific-state query. No evidence escalation, CandidateAction evaluation, database/model/network/Lambda/executor calls, or production imports yet.

## Remaining work

- Build the in-memory semantic twin and deterministic multi-hop query layer over adapter output.
- Implement evidence escalation/context slicing after semantic-twin P1/P2/P3/P6/P7 tests pass.
- Implement CandidateAction/DecisionEvaluation bridge after the evidence layer passes.
- Run frozen P1-P8 and issue PROMOTE_TO_INTEGRATION, REVISE, or REJECT.

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
