<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-wave1-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-wave1-execution-v1
- Title: Trusted Lambda route for Local EXTRACT Wave 1
- Status: COMPLETE
- Capsule schema: v2

## Goal

Expose exactly the merged research-engine Local EXTRACT Wave 1 workflow to the already-accepted two-A4500 Qwen3.5 execution envelope, install that exact route on Lambda, execute one bounded nine-paper benchmark, and retire the route owner after final receipt/cleanup evidence. This task does not own EXTRACT scientific design or production routing.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 4d580661a27f151e70f778111a88579e54de1c71
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Task complete. Return scientific ownership to research-engine-local-extract-redesign-v1. Do not rerun Wave 1; its fixed scientific decision is REJECT and the reusable Lambda execution path is accepted.

## Remaining work

- None.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
