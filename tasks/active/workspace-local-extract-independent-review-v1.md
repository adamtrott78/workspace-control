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
- Remote checkpoint: 43106fbd89c8a46493dee24f241fff4b5accbf2e
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 5d4a72f36f7407cdbe8662b53ac879861a2931e6
- Remote verified: true

## Next safe action

No reviewer-side blocker remains on INSUFFICIENT_BASELINE_GENERALIZATION. Owner may redesign the cross-paper teacher-blind baseline only, with the explicit objective of achieving a valid matched four-origin budget28 baseline on all nine papers without using teacher labels or the observed recovery outcomes. Independent review is required before implementation.

## Remaining work

- Wait for the EXTRACT owner to freeze a teacher-blind cross-paper baseline redesign that can instantiate the matched comparison on all nine papers.
- Do not review routine implementation/CI/trigger mechanics unless the baseline science changes.
- After the next genuine baseline or recovery result, independently audit exact run/artifact/result before further scientific selection.
- Do not permit proposition-level semantic generalization until a held-out multi-paper semantic benchmark exists.

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
