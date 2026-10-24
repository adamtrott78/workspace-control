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
- Remote checkpoint: 01bc9b762a5cd5f650189adf42500d52a6233802
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 8f03b818f415b33c3a3d0bd92d2c7396920013d6
- Remote verified: true

## Next safe action

Validate and merge this task-only project contract. Then begin reconstruction of the EXTRACT research history and external methodology research in parallel; do not mutate or block the active EXTRACT task.

## Remaining work

- Validate and merge the methodology project contract.
- Reconstruct the EXTRACT research history into explicit residual, hypothesis, mechanism, evidence, experiment, and decision states.
- Research external methodological foundations and synthesize methodology v0.1.
- Define and validate a machine-readable research-state schema.
- Retrospectively replay historical EXTRACT decisions without hindsight leakage.
- Run prospective shadow validation at future EXTRACT architecture/result boundaries without blocking EXTRACT.
- Make an evidence-based methodology promotion decision.
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
