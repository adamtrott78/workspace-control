<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-extract-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-extract-redesign-v1
- Title: Research Engine Mostly-Local EXTRACT Redesign v1
- Status: IN_PROGRESS
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
- Remote checkpoint: 831aff16cf2a44bbd834c93ecbb7e7fb99a6af20
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: a08d41b5de1721ef0a5427294ed8c06a8335120a
- Remote verified: true

## Next safe action

STOP after Wave 7A. Scientific verdict is WAVE7A_REJECT, but the oracle-query hypothesis remains supported. The source-aware generator preserved the full coarse page-recall ceiling; failure is intent coverage and atomicity. Resume only with an explicitly bounded coverage-guided hierarchical intent-decomposition design/experiment. Do not start Wave 7B, change production EXTRACT/VERIFY, train a reranker, or change generation-model family.

## Remaining work

- STOP after the Wave 7A WAVE7A_REJECT checkpoint; do not start Wave 7B automatically.
- Design a bounded coverage-guided hierarchical intent-decomposition phase that forces separate atomic questions for explicit scientific subslots instead of asking one Qwen pass to discover all intents freely.
- Preserve the existing coarse page route, authoritative proposition pool, BM25/BGE retrieval stack, Qwen3.5 model/runtime, production STANDARD Codex EXTRACT fallback, and accepted Qwen VERIFY while testing the new decomposition.
- Evaluate whether coverage-guided decomposition recovers the teacher atoms missed by Wave 7A: source-label classifier training, target-domain testing, negative-pair construction, scalability future work, and persistent-misclassification future work.
- Do not train a custom reranker or change generation-model family unless the coverage-guided decomposition experiment fails under a frozen gate.

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
