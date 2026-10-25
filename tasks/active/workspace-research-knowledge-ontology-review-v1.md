<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-research-knowledge-ontology-review-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-research-knowledge-ontology-review-v1
- Title: Research Knowledge Ontology Independent Review v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Independently review the frozen Research Knowledge Ontology v0.1 and 16-case blind replay benchmark for scientific validity, provenance/source-precedence correctness, anti-leak integrity, authority separation, generality, and non-tautological decision support before any projection implementation.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: de81b2a8c5bc30f5a7c22a1f3d28f9de0e3445c7
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 6a4cc30e8c33a54a8cca9eca82a4f1fa300ad7e8
- Remote verified: true

## Next safe action

Independently review architecture/research-knowledge-ontology.v0.1.json blob 9af5bea619ec5a2f83575b4c8d73d08922f05bdb and benchmarks/research_knowledge/research-state-replay-benchmark.v0.1.json blob 45bd39a722fc4ec24c8f29ce6c1d4eacda8c7998. Focus on source-precedence correctness, anti-leak/blind-replay integrity, non-tautological query semantics, exact provenance, scientific-state distinctions, and prevention of graph-created execution authority. Return NO_BLOCKING_FINDING or exact blockers; do not implement anything.

## Remaining work

- Perform independent review of the exact design and replay benchmark.
- Persist NO_BLOCKING_FINDING or exact blocking findings in this reviewer capsule/handoff.
- If NO_BLOCKING_FINDING, allow owner to consume the disposition; do not implement from the reviewer lane.

## Blockers / gates

- None beyond the owner task's hard implementation block pending this independent disposition.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-research-knowledge-ontology-review-v1.json

Start from the normal workspace-control root route.
Treat the reviewer capsule, owner capsule, exact durable Git state, exact design/benchmark blobs, and referenced evidence as the complete handoff.
Do not rely on previous conversation state.
Immediately perform the independent review in the capsule's next_safe_action.
Do not implement the ontology/projection.
