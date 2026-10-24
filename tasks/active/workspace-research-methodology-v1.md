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
- Remote checkpoint: 9fe9a21c9bb463e0a4196a5f10eb11468cebb5b2
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 3f433e3e31fd8fac3edf86f65cef9628635652cf
- Remote verified: true

## Next safe action

Run the frozen OUTCOME_PARTITION_EXHAUSTIVENESS_V0_2 meta-experiment exactly as specified using the generic validator and positive-control designs. Persist a separate result artifact. Do not mutate v0.1 or prescribe EXTRACT's next architecture.

## Remaining work

- Execute and validate the frozen outcome-partition meta-experiment; classify CANDIDATE_SUPPORTED, CANDIDATE_PARTIAL, CANDIDATE_REJECTED, or INVALID_META_EXPERIMENT without changing its gates.
- If supported, create a separate v0.2 candidate schema/validator representation; do not mutate v0.1 in place.
- Continue prospective validation of diagnostic-depth semantics and measure steady-state methodology overhead.
- Design a practical blind/isolated commitment protocol before claiming independent architecture-selection quality.
- Accumulate evidence beyond EXTRACT before canonical methodology promotion.
- If methodology concepts stabilize, create a separate ontology/research-knowledge integration task.

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
