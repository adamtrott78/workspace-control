<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-knowledge-action-ontology-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-knowledge-action-ontology-v1
- Title: Unified Knowledge-Action Ontology Architecture v1
- Status: CHECKPOINTED
- Capsule schema: v2

## Goal

Determine whether a provenance-preserving typed ontology/knowledge-graph substrate can unify research knowledge representation with executor decision/action semantics—so accumulated knowledge can help determine what should be done next—without conflating scientific evidence with policy authority, and produce a bounded architecture/benchmark plan before any production mutation.

## Workflow

- Repository: workspace-control
- Path: workflows/evidence-first-solution-research.v1.json
- Checkpoint: dbce355969e6378eef9effa2914393cc8add2e4c

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: f370bdc7afc8037dbb5f87a0228abfc011011329
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: ba9d09abf77af7280fdc5f5890dee1cb7a05ff67
- Remote verified: true

## Next safe action

Continue implementation only through the separate child task workspace-semantic-control-prototype-v1. This architecture task has completed its implementation handoff; preserve its frozen architecture/benchmark decisions as parent evidence. Keep Local EXTRACT independent.

## Remaining work

- Execute the separate child task workspace-semantic-control-prototype-v1; do not implement prototype code in this architecture task.
- When the MILCOM 2026 proceedings become public, independently bind the operator-provided title/affiliation to the published bibliographic record; this is provenance completion, not an architecture blocker.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-knowledge-action-ontology-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
