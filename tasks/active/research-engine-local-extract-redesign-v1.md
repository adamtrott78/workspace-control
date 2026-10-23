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
- Remote checkpoint: 8430baf2e6ec29296e812b6dbb4559b725154543
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: f3d5dc4f8cc5007d3159b232ae00317620a59de6
- Remote verified: true

## Next safe action

Create exactly one inert research-engine trigger PR from isolated implementation head 0abf32f0fa106c2b22a6f080341b0dadc4794f96, then issue exactly one `/local-extract-proposition-alignment-preservation <exact-trigger-head-sha>` comment. Observe the unique zero-generation run, evaluate only frozen ALIGNMENT_AUGMENT_STRONG/FEASIBLE/NEGATIVE, checkpoint exact artifact/report hashes and disposition, and close the trigger PR unmerged.

## Remaining work

- Create one inert research-engine trigger PR from exact isolated implementation head 0abf32f0fa106c2b22a6f080341b0dadc4794f96 with only a non-semantic marker.
- Issue exactly one `/local-extract-proposition-alignment-preservation <exact-trigger-head-sha>` comment and do not issue a second trigger.
- Evaluate only frozen ALIGNMENT_AUGMENT_STRONG/FEASIBLE/NEGATIVE, checkpoint run/artifact/report hashes immediately, and close trigger unmerged.
- Do not tune threshold/gates after result, promote fixed quota, execute rejected Qwen gap judge, train/download classifier, start Wave 7B, change production EXTRACT/VERIFY, or add ontology/semantic-control.

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
