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
- Current stage: post_wave6_codex_parity_diagnostics

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
- Remote checkpoint: 91ea8d7545838b822878f30dd8952b26e2a3ec3f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 265a7e4784209d411383cb09da4fe0adcf50f319
- Remote verified: true

## Current diagnostic contract

The user explicitly authorized a post-Wave-6 Codex-parity diagnostic/research phase. This is not Wave 7.

The phase must:
- recover or inventory preserved STANDARD Codex teacher text before creating new labels;
- retain the original six-claim lexical F1 benchmark unchanged for continuity;
- measure a stage-wise oracle ladder from parsed PDF through bounded 2-3 proposition evidence bundles and final normalization;
- measure evidence-span/atom-support retrieval at a fixed context budget rather than page recall alone;
- begin with zero-generation CPU/offline retrieval-window diagnostics before any external model download;
- classify the residual as RETRIEVAL, EVIDENCE_COMPOSITION, EVALUATION_GRANULARITY, MODEL_NORMALIZATION, or STOP before Wave 7;
- keep production EXTRACT, accepted Qwen VERIFY, and GitRunner/controller/provisioner/runtime unchanged.

## Next safe action

Execute the post-Wave-6 Codex-parity diagnostic stage: first recover/inventory historical Codex teacher text, then implement a zero-generation stage-wise oracle and fixed-budget retrieval/window diagnostic on the preserved corpus. Do not design, route, or execute Wave 7 yet. Do not change production EXTRACT, accepted Qwen VERIFY, GitRunner/controller/provisioner/runtime, or model family.

## Remaining work

- Recover or conclusively inventory preserved normalized STANDARD Codex outputs behind the 71 historical evidence objects; do not synthesize replacements until recovery avenues are exhausted.
- Implement a zero-generation stage-wise oracle harness on the preserved nine-paper corpus, with exact PDF/page/region/proposition/bounded-bundle support measurements and legacy lexical metrics.
- Run a CPU/offline retrieval-window diagnostic at a fixed context budget before selecting any dense, late-interaction, or cross-encoder dependency/model download.
- Research and shortlist external retrieval/reranking methods specifically against the measured failure mode, then benchmark only the smallest justified candidate set.
- Classify the remaining residual as RETRIEVAL, EVIDENCE_COMPOSITION, EVALUATION_GRANULARITY, MODEL_NORMALIZATION, or STOP; do not start Wave 7 before that decision.
- Keep the two Wave-6 CLAIM_SCHEMA rejects on arxiv:2609.20765 as a separate structured-output engineering issue; do not mistake them for the semantic bottleneck.

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
