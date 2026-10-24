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
- Remote checkpoint: bca2e37c95c680f1146c76273aaf2da1f6571ee8
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 07e2180975ca1bda4e7ac58cbec198e05cf5b733
- Remote verified: true

## Next safe action

Merge this exact composed acquisition/preservation pre-run checkpoint. Then issue exactly one `/local-extract-composed-acquisition-preservation f1c1d3d99fe4ad1a0101dd75a8a309572b326bc3` comment on research-engine PR #244 and bind the unique resulting run to that exact head. Do not issue a second trigger.

## Remaining work

- After this exact checkpoint merges, issue exactly one `/local-extract-composed-acquisition-preservation f1c1d3d99fe4ad1a0101dd75a8a309572b326bc3` comment on open research-engine PR #244.
- Bind the unique resulting workflow run to exact PR head f1c1d3d99fe4ad1a0101dd75a8a309572b326bc3 and inspect the uploaded report.
- Stop at COMPOSED_COMPLEMENTARITY_ROBUST / COMPOSED_COMPLEMENTARITY_FRAGILE / COMPOSITION_PARTIAL / COMPOSITION_NEGATIVE / COMPOSITION_COLLISION or operational INVALID_EXECUTION; do not tune or rerun after a valid scientific verdict.
- Persist the exact result and close PR #244 unmerged only after the result checkpoint is durable.
- After a genuine scientific verdict, obtain independent post-result review before selecting the next phase.

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
