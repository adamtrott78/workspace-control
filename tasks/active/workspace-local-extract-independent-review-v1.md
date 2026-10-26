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
- Remote branch: review-exact-provenance-post-result-v1
- Remote checkpoint: cd05211105620c3ad399a29a6f2fcfc8ba2e7398
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Perform the mandatory independent post-result review of the exact one-shot EXACT_PROVENANCE_BINDING_MICROBENCH_V1 result: research-engine PR #273 candidate 3eb6b391fcd2f6e2a44277771d0bcd8d26c7002d; implementation validation run 40269453984 PASS; scientific run 40411159582 / job 121881887321 / artifact 12693836542 / report sha256 fce8c958e0f91dffd9a740de2c71d1d451c6e3861e399f1afa550a50bd8f4f24. Audit the frozen all-or-nothing outcome and integrity/preservation evidence without rerun or posthoc gate changes. Persist NO_BLOCKING_FINDING or exact blocking findings in this reviewer task, then hand control back to owner task research-engine-local-extract-redesign-v1. No acceptance freeze or sealed holdout access.

## Remaining work

- Independently review the exact one-shot scientific result run 40411159582 against frozen EXACT_PROVENANCE_BINDING_MICROBENCH_V1; do not rerun, retune, or rewrite the gate.
- Verify Arm A: 7/7 case contracts, 3/3 false-positive reject/abstain, 3/4 true-support acceptance with exact provenance 3/4, no false-positive provenance attachments.
- Verify Arm B: 6/7 case contracts, 3/3 false-positive reject/abstain, 4/4 true-support acceptance with exact provenance 4/4, no false-positive provenance attachments; the sole contract failure is FP_TRAINING_PRETRAINING_NO_LABELS with ordinary failure reason INVALID_ENUM_OR_FIELD_TYPE.
- Verify all experiment-integrity and preservation controls remain PASS: evidence set 28->28 unchanged, prior supported atoms 9/9, frozen controls 7/7, teacher/PDF identities intact, 14 stateless model calls.
- Determine whether the frozen outcome EXACT_PROVENANCE_BINDING_PREMISE_REJECTED is correct and record bounded failure interpretation; distinguish Arm A semantic false-negative behavior from Arm B schema/contract brittleness.
- Do not authorize acceptance freeze, sealed holdout access, production EXTRACT/VERIFY changes, Wave 7B, or semantic-control coupling.
- After reviewer disposition is durable, owner research-engine-local-extract-redesign-v1 may consume it and only then choose the next scientific phase.

## Blockers / gates

- Owner next-phase scientific selection is blocked pending independent post-result review of run 40411159582.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-independent-review-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
