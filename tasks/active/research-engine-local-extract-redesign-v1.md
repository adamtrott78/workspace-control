<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-extract-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-extract-redesign-v1
- Title: Research Engine Mostly-Local EXTRACT Redesign v1
- Status: CHECKPOINTED
- Capsule schema: v2

## Goal

Return to first principles on research-engine EXTRACT and identify, benchmark, and if justified implement a provenance-preserving mostly-local extraction architecture that makes STANDARD Codex a rare ambiguity/failure fallback rather than the default, while reusing accepted local document/VERIFY infrastructure and not repeating approaches already invalidated by durable evidence.

## Workflow

- Repository: workspace-control
- Path: workflows/evidence-first-solution-research.v1.json
- Checkpoint: a9041372c50bf1258daea2236a3e62542a115117

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 0ff16a8d877a748e83f13b2d546d1b47a0b74744
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: ed666137ecf5c42950fb5eee2cd5ecc0d69f7c13
- Remote verified: true

## Next safe action

Implement the frozen PROPOSITION_ALIGNMENT_CERTIFIED_AUGMENTATION_DIAGNOSTIC_V1 from execution-isolated research-engine design head ca6ada76b1850a164ab964a9673a120a10d2f15e. Use DYNAMIC_SAME_PAGE_ALIGNMENT_SWAP_V1 exactly as frozen (same-page token_f1 >=0.40, certificate from another still-retained original baseline proposition, dynamic recomputation, baseline page-set preservation, residual RRF ordering, final budget 24), add focused tests and normal CI, then durable-checkpoint the implementation before exactly one zero-generation trigger.

## Remaining work

- Implement DYNAMIC_SAME_PAGE_ALIGNMENT_SWAP_V1 exactly as frozen from isolated research-engine design head ca6ada76b1850a164ab964a9673a120a10d2f15e.
- Add deterministic tests for same-page token-F1 certificate, dynamic recomputation, page-set preservation, residual ordering, and ALIGNMENT_AUGMENT_STRONG/FEASIBLE/NEGATIVE gates; run normal CI.
- Checkpoint the validated implementation, then create one inert trigger PR from the isolated implementation head and issue exactly one zero-generation diagnostic.
- Checkpoint the result immediately and close the inert trigger unmerged. No post-result threshold/gate tuning.
- Do not execute the rejected Qwen gap judge, promote fixed 20/4 quota, train/download a classifier, start Wave 7B, change production EXTRACT/VERIFY, or incorporate ontology/semantic-control mechanisms.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
