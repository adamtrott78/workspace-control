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
- Remote checkpoint: 8dd56b5c6d3859058437baa6a76692041f159977
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: abd55d31d2768f6d66d0aa187e90fa4950cfd26f
- Remote verified: true

## Current stage

freeze_benchmark_contract_and_holdout_corpus

## Next safe action

Run Workspace Control Validation on the frozen benchmark foundation. If clean, merge it. Then acquire exact source identities/hashes for all ten papers before finalizing pilot annotations.

## Remaining work

- Validate and merge the benchmark foundation.
- Acquire exact PDF hashes/page counts and canonical page-text identities for all ten fresh papers.
- Complete/finalize the two pilot annotations and run blind Pass-B adjudication.
- Create acceptance gold for the eight held-out papers without consulting Local EXTRACT outputs.
- Freeze gold and evaluate only a separately frozen Local EXTRACT candidate architecture.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/workspace-extract-semantic-benchmark-v1.json`

Start from the normal workspace-control root route.

Treat the authoritative task capsule, synchronized Markdown handoff, exact durable Git/runtime state, and referenced benchmark/source evidence as the complete handoff.

Do not rely on previous conversation state.

Keep `research-engine` and `research-engine-local-extract-redesign-v1` read-only. The benchmark is a parallel sibling lane.

Follow the capsule's `next_safe_action`.
