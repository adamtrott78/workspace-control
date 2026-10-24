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
- Remote checkpoint: 549f80ffb6fdbd6e31ce024fb66ce4a1e821a553
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: bf47d704019f7028b79841d8d5dc36254a519d1d
- Remote verified: true

## Next safe action

Merge this exact automatic-intent exposure pre-run checkpoint. Then issue exactly one `/local-extract-automatic-intent-exposure 96b39d2b94477f4c058bfb0425afa9f811c677f5` comment on research-engine PR #236 and bind the unique resulting run to that exact head. Do not issue a second trigger.

## Remaining work

- After this exact checkpoint merges, issue exactly one `/local-extract-automatic-intent-exposure 96b39d2b94477f4c058bfb0425afa9f811c677f5` comment on open research-engine PR #236.
- Bind the unique resulting workflow run to exact PR head 96b39d2b94477f4c058bfb0425afa9f811c677f5 and inspect the uploaded report.
- Stop at SHALLOW_SINGLE_INTENT_EXPOSURE, SHALLOW_DISTRIBUTED_EXPOSURE, DEEP_EXPOSURE, STATIC_INTENTS_INSUFFICIENT, or operational REPLAY_INCONSISTENT; do not tune or rerun after a valid scientific classification.
- Persist the exact result and close PR #236 unmerged only after the result checkpoint is durable.
- After a genuine scientific classification, obtain independent post-result review before selecting the next scientific phase.
- Do not reopen NLI/predicate-argument/AMR, change production EXTRACT/VERIFY, start Wave 7B, or emit semantic-control/RDF/ontology output.

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
