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

## Parent execution owner

research-engine-local-document-pipeline-v1

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 796dd9fb9c5fd25009d756a4fd42d53b85a5ac3d
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 5f6eec7b629b4746117f2f0a74d4531c642f8025
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 5f6eec7b629b4746117f2f0a74d4531c642f8025
- Local clean: true

## Current stage

architecture_selection_and_benchmark_contract

## Next safe action

Define the Local Evidence Agent v1 benchmark/architecture contract before downloading new heavyweight models. The contract should test a hierarchical mostly-local path: accepted sidecar/document structure -> lexical/vector retrieval and BGE-style reranking -> exact candidate spans/records (GLiNER2.5 and deterministic rules where useful) -> local atomic-claim normalization -> exact quote/page anchoring -> local scientific entailment/verification -> confidence gate; only unresolved units proceed to a stronger local agent candidate, and only its residuals fall through to STANDARD Codex. Compare role-specific candidates rather than whole-pipeline one-shot models, include Lift/NuExtract3 as bounded structured-extractor candidates and Qwen3.6-35B-A3B only as a hard-case feasibility candidate, and specify how Codex fallback outputs are retained as teacher data so fallback frequency can decrease over time.

## Remaining work

- Specify Local Evidence Agent v1 stage interfaces, provenance invariants, and confidence/fallback policy.
- Define a role-specific benchmark matrix using preserved EXTRACT jobs: candidate-region recall, atomic-claim precision/recall, normalized-form agreement, exact quote/page grounding, type agreement, unsupported-claim rate, latency/VRAM/RAM, and projected Codex fallback fraction.
- Choose the minimum candidate set for a first bounded prototype; prioritize reuse of the existing Qwen3.5-4B runtime in a narrower normalization/decision role where materially different from the failed one-shot EXTRACT architecture, plus lightweight retrieval/reranking/span models before any heavyweight download.
- Define teacher-data capture so every future Codex fallback can become supervised training/evaluation data for local candidate generation/normalization.
- Only after the contract is checkpointed, authorize at most the smallest necessary new model downloads/runtime bakeoffs.

## Blockers / gates

- None recorded.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
