<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-extract-semantic-benchmark-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-extract-semantic-benchmark-v1
- Title: Held-Out Multi-Paper Semantic Benchmark for Local EXTRACT
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Build an independently source-verified, held-out multi-paper semantic acceptance benchmark for Local EXTRACT so project success is measured by generalized claim/evidence quality rather than the one-paper 13-atom diagnostic. Keep active EXTRACT development scientifically independent and research-engine read-only while the benchmark corpus, annotation protocol, schemas, pilot annotations, adjudication rules, and final acceptance mapping are developed in workspace-control.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 4013b1d8b781b4ce11283508a0407d6e599a9969
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 44fbf6107db2e554a5e276a1862c02c66ffd1ab9
- Remote verified: true

## Next safe action

Run the dedicated source-freeze CI workflow on this branch, inspect its exact manifest, persist the manifest into workspace-control, and validate all ten frozen source identities before pilot adjudication.

## Remaining work

- Run the dedicated source-freeze CI job and persist exact PDF SHA-256, page counts, and canonical page-text hashes for all ten fresh papers.
- Complete/finalize the two pilot annotations against the frozen source identities and run Pass-B adjudication.
- Create source-first acceptance gold for the eight held-out papers without consulting Local EXTRACT outputs.
- Freeze acceptance gold and evaluate only a separately frozen Local EXTRACT candidate architecture.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-extract-semantic-benchmark-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
