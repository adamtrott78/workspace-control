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
- Remote checkpoint: cd26f0cb38363f994640f1cfb08aa1a01b9b299d
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 8f03b818f415b33c3a3d0bd92d2c7396920013d6
- Remote verified: true

## Next safe action

No reviewer-side mutation is currently required. The AMR rejection is independently confirmed. Wait for the EXTRACT owner to durably checkpoint the result and choose the next scientific phase; re-engage only at the next genuinely new architecture boundary or scientific-result boundary. Do not influence routine execution mechanics.

## Remaining work

- Wait for the EXTRACT owner to durably checkpoint the AMR scientific result and select its next evidence-first scientific phase under its own authority.
- Review the next genuinely new scientific architecture before implementation, or the next genuine scientific result before phase selection.
- Do not review routine CI, packaging, route, trigger, or cleanup mechanics unless they materially alter the frozen experiment.
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
