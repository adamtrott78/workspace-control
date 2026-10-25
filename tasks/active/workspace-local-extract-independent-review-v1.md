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

Owner may implement exactly ALL_NINE_FIXED_BASELINE_RECOVERY_COMPARISON_V1 from research-engine@05b8149cbfa81d7ceafadf2b5ce867bd687cfa14 / design blob 86a21acbf2d50e5fb42ed1e1a4e3287d2a82bd57. Re-engage reviewer only if science changes or after the genuine result. The sealed acceptance benchmark remains off-limits.

## Remaining work

- Wait for the EXTRACT owner to implement and execute exactly ALL_NINE_FIXED_BASELINE_RECOVERY_COMPARISON_V1.
- Do not review routine implementation/CI/packaging/trigger mechanics unless they materially alter the frozen corrected comparison science.
- After the genuine corrected all-nine comparison result, independently audit the exact run/artifact/result before next-phase selection.
- Keep the sealed acceptance benchmark uninspected until the owner separately freezes an acceptance candidate.

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
