<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-document-pipeline-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-document-pipeline-v1
- Title: Research Engine Local Document Intelligence and Compute Offload v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, benchmark, and integrate a provenance-preserving local document-intelligence pipeline that converts content-addressed research PDFs into reusable LLM-ready paper packages, minimizes paid/plan semantic usage and repeated PDF interpretation, and systematically evaluates every research-engine stage for safe deterministic or local-model offload before production deployment on the Lambda.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 134d60630a1bf16499fee169f28456a670de343f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 8c875a62d44e91ed91207cdc78d715acb0909346
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 8c875a62d44e91ed91207cdc78d715acb0909346
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. Treat research-engine main@8c875a62d44e91ed91207cdc78d715acb0909346 as the validated document-pipeline/A-B baseline. Begin research_pipeline_localization_matrix_validation by inspecting benchmarks/document_intelligence/localization-matrix.v1.json plus the current worker/orchestration mappings, then reconcile every research job type against measured evidence. Preserve the decision that authoritative-PDF hydration remains the EXTRACT/VERIFY production baseline; paper-package context must not silently replace it. Validate local deterministic placement, semantic executor placement, shared-model ownership, provenance/fidelity boundaries, and resource/token evidence before production acceptance. Do not start the research daemon or sustained research.

## Remaining work

- Validate the localization matrix end-to-end against the now-measured document pipeline: keep authoritative-PDF hydration for EXTRACT/VERIFY, retain local deterministic document compilation/routing/escalation, and keep heavyweight formula/table models behind the shared local inference broker.
- Review each research pipeline operation (DISCOVERY, ACQUIRE, EXTRACT, VERIFY, SYNTHESIZE, GAP_GENERATE, CHECKPOINT, HUMAN_REVIEW) for the intended local-vs-semantic execution boundary and verify no stale assumption expects paper-package context to replace authoritative PDF hydration.
- Measure or reuse existing token/latency/resource evidence for the remaining semantic operations and confirm that localizing deterministic work does not reduce evidence fidelity or provenance.
- Complete final Lambda production acceptance, including daemon integration, bounded concurrency, database/runtime dependencies, operator recovery behavior, and CodeFormulaV2 licensing/deployment review.
- Only after those gates pass consider enabling sustained research.

## Blockers / gates

- CodeFormulaV2 deployment/redistribution obligations still require final license/deployment review before sustained production enablement.
- The broader research_pipeline_localization_matrix_validation stage has not yet been completed; end-to-end production placement for each research operation still requires explicit validation.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
