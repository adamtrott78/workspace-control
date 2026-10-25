<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-extract-semantic-benchmark-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-extract-semantic-benchmark-v1
- Title: Held-Out Multi-Paper Semantic Benchmark for Local EXTRACT
- Status: BLOCKED_EVIDENCE
- Capsule schema: v2

## Goal

Build an independently source-verified, held-out multi-paper semantic acceptance benchmark for Local EXTRACT so project success is measured by generalized claim/evidence quality rather than the one-paper 13-atom diagnostic. Keep active EXTRACT development scientifically independent and research-engine read-only while the benchmark corpus, annotation protocol, schemas, pilot annotations, adjudication rules, and final acceptance mapping are developed in workspace-control.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: a0f4e69281341fa3eb9f9578e1f4a789db7f59d6
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 44fbf6107db2e554a5e276a1862c02c66ffd1ab9
- Remote verified: true

## Next safe action

Do not reveal the sealed acceptance gold or run Local EXTRACT on the eight acceptance papers yet. Wait for the owning EXTRACT task to freeze a specific acceptance candidate. Then verify gold commitment 98a36f7d51df13bb9bc4541e8c91fb96ac7db5ab0982a69bda38a74e4e789e0a and authorize exactly one held-out evaluation.

## Remaining work

- Wait for the owning EXTRACT task to freeze a candidate architecture for held-out acceptance.
- After candidate freeze, verify the sealed gold commitment before reveal.
- Run exactly one held-out acceptance evaluation across the eight papers and map results to the original precision/provenance/coverage/completion/fallback/VERIFY/economics promotion gates.
- If acceptance results materially influence further architecture tuning, require a new untouched holdout for any later unbiased promotion claim.

## Blockers / gates

- AWAIT_FROZEN_EXTRACT_ACCEPTANCE_CANDIDATE: A Local EXTRACT architecture must be separately frozen by the owning research task before the sealed acceptance gold may be revealed or the held-out benchmark executed. Resolve only when the owner checkpoints an acceptance candidate and explicitly hands off one-shot held-out evaluation authority.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-extract-semantic-benchmark-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
