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
- Remote checkpoint: ea20ee618251063d12ec13d0de92e35bff039a19
- Remote verified: true

## Next safe action

Implement only implement_action_candidate_and_decision_bridge from research-engine checkpoint ea20ee618251063d12ec13d0de92e35bff039a19. Add pure CandidateActionV1 proposal and DecisionEvaluationV1 evaluation code under prototypes/semantic_control/** plus tests under tests/semantic_control/**. Candidate actions must always remain UNDECIDED. Only authoritative NORMATIVE policy observations may produce ALLOW; epistemic/model claims of permission must be ignored. Missing authority yields ABSTAIN; explicit deny yields DENY; no executor invocation or receipt creation is allowed. Prove frozen gpu-heavy DENY and Wave7B ABSTAIN plus a synthetic positive-policy ALLOW case.

## Remaining work

- Implement CandidateActionV1 generation and fail-closed DecisionEvaluationV1 over frozen policy/task fixtures.
- Run frozen P1-P8 integrated benchmark and issue PROMOTE_TO_INTEGRATION, REVISE, or REJECT.

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
