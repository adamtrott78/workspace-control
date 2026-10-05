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

Wait only for the two already-running contract validations: research-engine PR #95 and workspace-control PR #70. If both pass, merge them, verify the resulting canonical SHAs, bind this task to the exact merged `workflows/evidence-first-solution-research.v1.json` identity, mark `architecture_selection_and_benchmark_contract` VALIDATED, and begin Phase 1 of `bounded_local_extract_prototype`: an offline zero-materialization preserved-EXTRACT dataset adapter plus deterministic lexical/section retrieval baseline and exact teacher-quote/page recall measurement. Do not download any new heavyweight model and do not change production VERIFY during Phase 1.

## Remaining work

- Land and pin the reusable workspace-control evidence-first-solution-research workflow (PR #70) so future project/chat architecture decisions can invoke the same method before implementation.
- Land the research-engine Local Evidence Agent v1 contract (PR #95). Its first CI attempt was cancelled before runner assignment with zero steps; the unchanged job has been retried.
- Phase 1 — offline substrate/retrieval: build a zero-materialization adapter over preserved EXTRACT jobs, measure deterministic lexical/section retrieval and exact teacher-quote/page recall before adding any model.
- Phase 2 — first-wave local evidence path: add exact candidate-span handling, use the existing certified Qwen3.5-4B only for bounded quote-to-atomic-claim normalization, and add an independent local scientific verifier/completeness audit. Do not download a new heavyweight model yet.
- Phase 3 — measure the combined system: claim precision/coverage, grounding/page/type agreement, unsupported-claim rate, job-local completion fraction, Codex fallback fraction, latency/VRAM/RAM, and remote token suppression.
- Phase 4 — residual-only escalation: add GLiNER2.5 / compact reranker / scientific verifier components only where measured first-wave residuals justify them; open NuExtract3, Lift 9B, or Qwen3.6-35B-A3B one at a time only if lighter decomposition cannot meet gates.
- Phase 5 — teacher adaptation: retain verified Codex fallback cases as versioned training/evaluation data with paper-level holdouts; use them to reduce fallback frequency without contaminating evaluation.
- Phase 6 — VERIFY impact measurement: after EXTRACT meets promotion gates, compare the new pre-materialization local verifier with current post-materialization page-scoped Qwen VERIFY. Preserve current VERIFY unchanged until evidence shows whether it should stay independent, narrow to residual/sample audit, or be separately redesigned.
- Phase 7 — production integration only after passing gates: local-first EXTRACT with Codex STANDARD as rare fallback, empirical fallback telemetry, accepted VERIFY behavior, and separate Lambda acceptance.

## Blockers / gates

- research-engine PR #95 contract CI retry is pending after the first attempt was cancelled in queue with runner_id=0 and zero executed steps; this is an external CI scheduling boundary, not a code/test failure.
- workspace-control PR #70 full-integration validation is pending before the shared evidence-first workflow can be pinned by this task.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
