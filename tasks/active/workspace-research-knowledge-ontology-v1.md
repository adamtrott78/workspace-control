<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-research-knowledge-ontology-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-research-knowledge-ontology-v1
- Title: Research Knowledge Ontology v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Build and validate a read-only, provenance-preserving scientific-state knowledge projection that reconstructs residuals, hypotheses, assumptions, mechanism families, frozen experiments, executions, results, interpretations, independent reviews, belief updates, authority boundaries, and candidate next actions from durable workspace-control and research-engine evidence—without becoming a new source of scientific truth, policy authority, EXTRACT behavior, or executor permission.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: research-knowledge-ontology-v1-design
- Remote checkpoint: 3d8b2d4f2bf646ad1eb6e0b8b8e3b4331d740af1
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 13a129ef820c611adf6a6ca70598df1e67d56efc
- Remote verified: true

## Next safe action

Engage an independent reviewer on architecture/research-knowledge-ontology.v0.1.json blob 66fce530c9539ddc8e1da15e1581d7b5d32fcca4 and benchmarks/research_knowledge/research-state-replay-benchmark.v0.1.json blob 6aa796b49209b87c3fc5cc4351122eb4b679cb3b. Reviewer should test source-precedence correctness, epistemic/normative/execution separation, verdict-vs-posthoc and negative-vs-invalid distinctions, rejected-mechanism reopening semantics, and whether CandidateAction/DecisionEvaluation can remain useful without graph-created authority. No implementation before disposition.

## Remaining work

- Obtain independent review of the exact frozen ontology/replay contract.
- If NO_BLOCKING_FINDING, implement only the read-only deterministic projection and model-free replay evaluator in workspace-control.
- Run the frozen 16-case replay benchmark and require all exact/provenance/safety gates.
- Do not integrate with live EXTRACT or production semantic-control in this task.

## Blockers / gates

- Independent pre-implementation review is required for exact design blob 66fce530c9539ddc8e1da15e1581d7b5d32fcca4 and replay-benchmark blob 6aa796b49209b87c3fc5cc4351122eb4b679cb3b before any projection implementation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-research-knowledge-ontology-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
