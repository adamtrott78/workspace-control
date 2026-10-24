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
- Remote checkpoint: 4961e36ad31f8f944486219e7dd0a7e4ac76535a
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 5ba005d9e0a1ee79056e8e4f4377c36903c09381
- Remote verified: true

## Next safe action

Implement exactly AUTOMATIC_INTENT_EXPOSURE_DIAGNOSTIC_V1 from research-engine@5ba005d9e0a1ee79056e8e4f4377c36903c09381. Replay only the frozen accepted source-aware and author-anchored intents with BM25_DIRECT on arxiv:2403.04036, evaluate fixed depths 1/3/5/8/12 using frozen teacher anchors only after ranking, reproduce the known author top-24 e1.a/e6.a support as a consistency check, and make no model/generation/production changes.

## Remaining work

- Implement AUTOMATIC_INTENT_EXPOSURE_DIAGNOSTIC_V1 exactly as frozen on arxiv:2403.04036 with deterministic tests and no generation/model changes.
- Run normal CI and persist the exact implementation checkpoint before scientific execution.
- Create an inert exact-SHA trigger anchor and authorize exactly one valid exposure run.
- Stop at SHALLOW_SINGLE_INTENT_EXPOSURE, SHALLOW_DISTRIBUTED_EXPOSURE, DEEP_EXPOSURE, STATIC_INTENTS_INSUFFICIENT, or operational REPLAY_INCONSISTENT.
- After a genuine scientific exposure classification, obtain independent post-result review before designing/implementing the mechanism family authorized by that classification.
- Do not tune prior frontiers, reopen NLI/predicate-argument/AMR, alter production EXTRACT/VERIFY, start Wave 7B, or emit semantic-control/RDF/ontology output.

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
