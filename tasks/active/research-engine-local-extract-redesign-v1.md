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
- Remote checkpoint: 5d3938ffff5bdea2ddfb03ae79c203a95a3bce05
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 14acd0aeb6cda93f0d82bc129649a73dba21a200
- Remote verified: true

## Next safe action

Merge this exact neighborhood-rescue pre-run checkpoint. Then issue exactly one `/local-extract-adjacent-proposition-rescue 7b53deccf4e8b5a34aa30bc0472493e189ad5f44` comment on research-engine PR #248 and bind the unique resulting run. Do not issue a second trigger.

## Remaining work

- After this checkpoint merges, issue exactly one `/local-extract-adjacent-proposition-rescue 7b53deccf4e8b5a34aa30bc0472493e189ad5f44` comment on PR #248.
- Bind the unique resulting workflow run to the exact trigger head and inspect the report/artifact.
- Stop at the frozen disjoint neighborhood-rescue verdict; no valid-result rerun or tuning.
- Persist the result, close PR #248 unmerged after result checkpoint is durable, and obtain independent post-result review.

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
