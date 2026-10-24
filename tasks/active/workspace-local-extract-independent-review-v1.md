<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-independent-review-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-independent-review-v1
- Title: Local EXTRACT Independent Review v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Provide an independent, durable review/support lane for research-engine-local-extract-redesign-v1 while preserving a single EXTRACT scientific owner. Consume exact EXTRACT checkpoints, artifacts, benchmark/result evidence, and frozen gates; identify methodological or contract inconsistencies; assess downstream compatibility with the opaque semantic-control integration socket; and publish bounded review findings in workspace-control without changing EXTRACT science, implementation, acceptance criteria, or semantic-control production behavior.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 2f4d0c64d6153b737bc606bd81f7a8119cbb1220
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 8f03b818f415b33c3a3d0bd92d2c7396920013d6
- Remote verified: true

## Next safe action

No reviewer-side mutation is currently required. Wait for a new durable EXTRACT design/result checkpoint or a future explicit AMR execution-authority checkpoint; then re-read the exact EXTRACT evidence and review it. Current NO_BLOCKING_FINDING does not authorize execution.

## Remaining work

- Wait for a new durable EXTRACT design/result checkpoint or a separately authorized future AMR execution checkpoint.
- At that checkpoint, re-read the authoritative EXTRACT capsule and exact evidence before reviewing.
- If a genuine accepted EXTRACT output contract eventually appears, audit bindability for semantic-control integration.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-independent-review-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
