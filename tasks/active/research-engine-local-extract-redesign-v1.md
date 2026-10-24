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
- Remote checkpoint: 2ae7eaedac665700376684ce4af6fcbf280f5674
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d058ee664c3b8be765258abc626dc667589618b7
- Remote verified: true

## Next safe action

Merge this exact facet planner pre-run checkpoint. Then issue exactly one `/local-extract-facet-reserved-evidence-planner 61c57dd72f0cb174908e5648405d87e89c0ec904` comment on research-engine PR #240. Do not issue a second trigger.

## Remaining work

- After this checkpoint merges, issue exactly one frozen facet planner trigger on PR #240.
- Bind the unique resulting run to exact head 61c57dd72f0cb174908e5648405d87e89c0ec904 and inspect the report.
- Stop at the frozen verdict; no post-result tuning or valid rerun.
- Persist the result, close PR #240 unmerged after result checkpoint, and obtain independent post-result review.

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
