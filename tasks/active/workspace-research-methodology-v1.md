<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-research-methodology-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-research-methodology-v1
- Title: Evidence-First Research Methodology v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Develop and validate a reusable outer-loop research methodology for AI/software research that converts residual problems into explicit competing hypotheses, evidence-backed mechanism choices, discriminating experiments, preregistered interpretation rules, belief updates, and stopping/reopening rules. Use the Local EXTRACT research history as a read-only retrospective and live shadow case study, while keeping EXTRACT scientifically independent and deferring ontology/semantic-control integration until the methodology itself is validated.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: fbb43982c41355d0c4d9a491a8363b5f3f954f23
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 3f433e3e31fd8fac3edf86f65cef9628635652cf
- Remote verified: true

## Next safe action

Wait for the owning EXTRACT task to produce the genuine NONDESTRUCTIVE_EVIDENCE_FRONTIER_DIAGNOSTIC_V1 scientific result. Then compare that result and the owner's next-phase interpretation against the already-frozen pre-result shadow, without changing the shadow prediction and without blocking or mutating EXTRACT.

## Remaining work

- Validate the full methodology v0.1 artifact set and frozen pre-result evidence-frontier shadow snapshot.
- After NONDESTRUCTIVE_EVIDENCE_FRONTIER_DIAGNOSTIC_V1 produces a genuine result, compare that result and the EXTRACT owner's next decision against the frozen shadow interpretation without changing the prediction.
- Accumulate at least one future architecture-selection shadow case that was not shaped by methodology-side advice.
- Measure residual clarity, hypothesis breadth, experiment discrimination, falsifiability, premise-reuse control, invariant preservation, failure informativeness, research efficiency, and coordination overhead.
- Make an evidence-based methodology promotion decision only after prospective evidence exists.
- If warranted, create a separate ontology/research-knowledge integration task.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-research-methodology-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
