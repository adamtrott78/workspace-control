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
- Remote checkpoint: 80da2cae9f8d80a7e7049a9b5339807becc54a98
- Remote verified: true

## Next safe action

Create the research-engine prototype branch from exact checkpoint 80da2cae9f8d80a7e7049a9b5339807becc54a98 and perform only stage freeze_contract_and_fixtures: inspect the exact authoritative fixture candidates, write a provenance-pinned fixture manifest and V1 interface contracts under benchmarks/semantic_control/**, and add contract/fixture tests under tests/semantic_control/**. Do not implement the semantic engine until those contracts and expected-answer fixtures are frozen.

## Remaining work

- Freeze the exact fixture manifest and V1 interface schemas before writing semantic-engine code.
- Implement deterministic adapters and canonical semantic-manifest hashing only after fixture/contract freeze.
- Implement/query the in-memory semantic twin, then evidence escalation/context slicing, then action-candidate/DecisionEvaluation in that order.
- Run the frozen P1-P8 benchmark and issue PROMOTE_TO_INTEGRATION, REVISE, or REJECT without touching production paths.

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
