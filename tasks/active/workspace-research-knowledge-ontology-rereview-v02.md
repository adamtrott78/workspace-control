<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-research-knowledge-ontology-rereview-v02.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-research-knowledge-ontology-rereview-v02
- Title: Research Knowledge Ontology v0.2 Independent Re-review
- Status: IN_PROGRESS
- Capsule schema: v2

## Exact review target

- Owner: `workspace-control@f321f21ff732b3c4e1f5e92051f8cb113e212998`
- Owner blob: `416e0c5b9ac6ce73cb34e8c86a0059a6622d67db`
- Design: `architecture/research-knowledge-ontology.v0.2.json`
- Design blob: `039fd2f888fb1abfb663c841df3425e2aa69fb74`
- Benchmark: `benchmarks/research_knowledge/research-state-replay-benchmark.v0.2.json`
- Benchmark blob: `c73f6f531a05386c1177a2709690ad2b06739ea9`

Prior review:
`workspace-control@706957531271486b7df510933297fa9169134a65|design@9af5bea619ec5a2f83575b4c8d73d08922f05bdb|benchmark@45bd39a722fc4ec24c8f29ce6c1d4eacda8c7998:BLOCKING_FINDING`

## Next safe action

Independently review architecture/research-knowledge-ontology.v0.2.json blob 039fd2f888fb1abfb663c841df3425e2aa69fb74 and benchmarks/research_knowledge/research-state-replay-benchmark.v0.2.json blob c73f6f531a05386c1177a2709690ad2b06739ea9 against the five prior blockers. Verify non-vacuous INVALID_EXECUTION and contradiction coverage, 10/10 required query-family coverage, operational anti-hardcoding through same-query/different-graph pairs plus deterministic relabeling, and exact deterministic canonical scoring. Also verify no regression of authority separation. Return NO_BLOCKING_FINDING or exact blockers; do not implement anything.

## Remaining work

- Perform independent re-review of exact v0.2 design and benchmark.
- Persist NO_BLOCKING_FINDING or exact result-affecting blockers.
- Do not implement from reviewer lane.

## Restrictions

- No implementation.
- No owner/design/benchmark mutation.
- No EXTRACT mutation.
- No sealed benchmark access.
- No production/policy/integration change.

## Fresh-chat initialization

@GitHub @Heartbeat

https://github.com/adamtrott78/workspace-control

Continue the durable independent-review task:
`tasks/active/workspace-research-knowledge-ontology-rereview-v02.json`

Task ID:
`workspace-research-knowledge-ontology-rereview-v02`

Start from the normal workspace-control root route.
Treat the reviewer capsule, owner capsule, prior BLOCKING_FINDING, exact durable Git state, and exact corrected v0.2 design/benchmark blobs as the complete handoff.
Do not rely on previous conversation state.
Immediately begin Workspace Heartbeat with the same real reviewer task ID.
Follow the capsule's next_safe_action.
Do not implement the ontology/projection.
