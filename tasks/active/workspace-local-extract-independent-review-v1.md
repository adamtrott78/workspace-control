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
- Remote checkpoint: cf3fb784bb2e518dc82a78de7f7d714c64a74bfe
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 6cd3eb3b38efbf2670a548f5ec052d8129f48067
- Remote verified: true

## Next safe action

Owner must make a design-only correction to FACET_RESERVED_EVIDENCE_PLANNER_V1: scientific NEGATIVE requires a valid safe replay with e1.a absent through budget32; safety/provenance/replay failures must be no-verdict. Re-engage this reviewer on the corrected exact design before implementation.

## Remaining work

- Wait for the owner to correct the frozen interpretation so safety/provenance/replay failures are no-verdict rather than scientific NEGATIVE.
- Review the corrected exact design before implementation.
- After a valid scientific result, audit the exact run/artifact/verdict before next-phase selection.

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
