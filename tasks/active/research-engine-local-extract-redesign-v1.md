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
- Remote checkpoint: b004931b8ccc7e4eb9977ba4ba080cab90d36532
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: ba9d09abf77af7280fdc5f5890dee1cb7a05ff67
- Remote verified: true

## Next safe action

STOP after valid Wave 7A.2. Scientific verdict is WAVE7A2_REJECT, while the oracle-query hypothesis remains supported. Evidence-conditioned answerability preserved page coverage but regressed because it allocated intents to background/definition/citation facts rather than high-salience scientific contributions. Resume with targeted research/design for scientific salience/contribution-aware intent generation; do not start Wave 7B, change production EXTRACT/VERIFY, train a reranker, or change generation-model family.

## Remaining work

- STOP after the valid Wave 7A.2 WAVE7A2_REJECT checkpoint; do not start Wave 7B automatically.
- Before another experiment, research methods for scientific salience/contribution modeling: contribution-sentence identification, scientific discourse/rhetorical-role classification, argument/claim mining, novelty/result/limitation prioritization, and salience-aware question generation.
- Design the next bounded experiment around allocating intent budget to high-salience contribution/evaluation evidence rather than to every answerable proposition; evidence answerability alone is now a rejected objective.
- Preserve the existing coarse page route, authoritative proposition pool, BM25/BGE retrieval stack, Qwen3.5 model/runtime, top-24 budget, production STANDARD Codex EXTRACT fallback, and accepted Qwen VERIFY during the first salience-aware experiment.
- Keep BM25 as a first-class cheap retriever: the repaired one-shot source-aware control reached 7/13 teacher atoms with BM25 and recovered all three historical hard misses.
- Do not train a custom reranker or change generation-model family unless a salience-aware intent architecture is tested under a frozen gate and still fails.
- Treat semantic intent deduplication and coverage of high-salience atomic facts as secondary design requirements; do not solve them by unrestricted query proliferation.

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
