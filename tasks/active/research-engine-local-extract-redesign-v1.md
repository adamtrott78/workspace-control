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
- Remote checkpoint: a9041372c50bf1258daea2236a3e62542a115117
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 2de0fb0c0049499507661ae5d3e4bea0f5c41720
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 5f6eec7b629b4746117f2f0a74d4531c642f8025
- Local clean: True

## Next safe action

Implement Phase 1 on research-engine main 2de0fb0c0049499507661ae5d3e4bea0f5c41720: add a zero-materialization preserved-EXTRACT dataset adapter over the existing nine-paper run, plus a deterministic lexical/section retrieval baseline that ranks exact source regions and measures teacher quote/page recall. Reuse PaperPackageABPlanner/ResearchContextHydrator and current provenance contracts; do not call SemanticResultMaterializer, do not change production routing/VERIFY, and do not download or invoke a new model. Land unit tests and a read-only benchmark entrypoint first. After CI passes, run the benchmark against the preserved Lambda dataset through an already-authorized bounded execution path or add the smallest separately reviewed execution route required; do not widen generic gpu-heavy.

## Remaining work

- Phase 1 — offline substrate/retrieval: build a zero-materialization adapter over preserved EXTRACT jobs, measure deterministic lexical/section retrieval and exact teacher-quote/page recall before adding any model.
- Phase 2 — first-wave local evidence path: add exact candidate-span handling, use the existing certified Qwen3.5-4B only for bounded quote-to-atomic-claim normalization, and add an independent local scientific verifier/completeness audit. Do not download a new heavyweight model yet.
- Phase 3 — measure the combined system: claim precision/coverage, grounding/page/type agreement, unsupported-claim rate, job-local completion fraction, Codex fallback fraction, latency/VRAM/RAM, and remote token suppression.
- Phase 4 — residual-only escalation: add GLiNER2.5 / compact reranker / scientific verifier components only where measured first-wave residuals justify them; open NuExtract3, Lift 9B, or Qwen3.6-35B-A3B one at a time only if lighter decomposition cannot meet gates.
- Phase 5 — teacher adaptation: retain verified Codex fallback cases as versioned training/evaluation data with paper-level holdouts; use them to reduce fallback frequency without contaminating evaluation.
- Phase 6 — VERIFY impact measurement: after EXTRACT meets promotion gates, compare the new pre-materialization local verifier with current post-materialization page-scoped Qwen VERIFY. Preserve current VERIFY unchanged until evidence shows whether it should stay independent, narrow to residual/sample audit, or be separately redesigned.
- Phase 7 — production integration only after passing gates: local-first EXTRACT with Codex STANDARD as rare fallback, empirical fallback telemetry, accepted VERIFY behavior, and separate Lambda acceptance.

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
