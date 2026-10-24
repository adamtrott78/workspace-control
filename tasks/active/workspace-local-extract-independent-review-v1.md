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
- Remote checkpoint: c49c3374a1bcdaabbf013cbc92c92d80705928b4
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: eb492ee8284fc9198bb8d931e3591c870b34ea12
- Remote verified: true

## Next safe action

Validate and merge this task-only review contract. Then re-read the latest EXTRACT capsule before the first substantive review; review only exact durable checkpoints and publish findings here without mutating EXTRACT or integration.

## Remaining work

- Validate and merge this independent review contract.
- On each meaningful new EXTRACT design/result checkpoint, re-read the authoritative EXTRACT capsule and exact evidence before reviewing.
- Persist only material review findings; do not duplicate the EXTRACT owner's scientific work.
- When an accepted EXTRACT output contract eventually appears, audit bindability and hand exact evidence back to workspace-semantic-control-integration-v1.

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
