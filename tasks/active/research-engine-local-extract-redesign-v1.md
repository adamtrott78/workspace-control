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
- Remote checkpoint: de705dda17ce62ed234866d51b03733a364ec66f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 1766cc6d11c9e65265a90579342fbac4888d0274
- Remote verified: true

## Next safe action

Merge this exact COMPLEMENTARY_STRUCTURAL_RECOVERY result checkpoint, close research-engine PR #257 unmerged, and re-engage workspace-local-extract-independent-review-v1 on run 40151063835 / artifact 12581733721 / report sha256:5f83398baba06cb2c96a51e9252ced763a760736e563a4994e7e4f09c60ff52e. Do not freeze the hybrid or acceptance candidate before that review is durable.

## Remaining work

- Obtain independent post-result review of run 40151063835 / artifact 12581733721 / report sha256 5f83398baba06cb2c96a51e9252ced763a760736e563a4994e7e4f09c60ff52e before freezing a hybrid design.
- After this result checkpoint merges, close research-engine PR #257 unmerged and do not retrigger.
- If reviewer finds no blocking issue, design the smallest deterministic hybrid recovery operator using the same fixed all-nine baseline and the two unchanged structural arms; freeze and review before implementation.
- Do not add deeper retrieval merely from the allocation-only case: its exact recovery is SHALLOW_FRONTIER and depth-extension exact recoveries are zero.
- Keep the sealed acceptance benchmark uninspected. Do not declare ACCEPTANCE_CANDIDATE_FROZEN until a reproducible end-to-end candidate is independently justified by development evidence.

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
