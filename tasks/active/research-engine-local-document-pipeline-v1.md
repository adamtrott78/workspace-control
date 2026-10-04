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
- Remote checkpoint: 0e5b1464c5307b9b1824618b6e5cff0f13485146
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 0e5b1464c5307b9b1824618b6e5cff0f13485146
- Local clean: true

## Next safe action

Keep sustained research disabled and leave research-engine-daemon.service inactive/dead unless a later bounded gate explicitly owns its lifecycle. Treat research-engine main@0e5b1464c5307b9b1824618b6e5cff0f13485146 as the validated bounded-production baseline. Begin residual_escalation_and_local_semantic_fallbacks by reading the existing localization matrix, adaptive routing/table/formula evidence, sidecar telemetry, and benchmark corpus contracts. First produce an explicit residual taxonomy plus benchmark/promotion contract; do not download or globally enable OCR/VLM/local-agent models yet. The contract must distinguish scan/text residuals, formula/table residuals already served by specialized models, figure/chart visual semantics, layout anomalies, and semantic EXTRACT/VERIFY ambiguity; preserve authoritative PDF/page/region provenance; and define the intended escalation ladder deterministic/native+structure -> specialized local model -> targeted OCR/VLM/local semantic candidate when justified -> Codex -> human. Then identify the minimum additional corpus cases and candidate families needed for measured experiments without reopening the closed broad parser bakeoff.

## Remaining work

- Define an explicit residual taxonomy from existing benchmark/production evidence: textless/scanned pages, low-confidence OCR/text recovery, formula residuals after CodeFormulaV2, table residuals after FAST/ACCURATE/Paddle, uncaptioned/semantic figures and charts, layout/reading-order anomalies, and semantic extraction/verification ambiguity.
- Define stage-by-stage promotion/fallback gates with authority/provenance requirements, confidence thresholds, failure semantics, GPU/RAM/latency ceilings, and remote-token/allowance accounting.
- Add only the benchmark cases needed to exercise missing residual classes, especially scan/image-only pages and semantically rich figure/chart regions; do not reopen the closed general parser bakeoff.
- Benchmark candidate local recovery tiers in increasing cost order. OCR should be tested only on textless/scan residuals; local multimodal/VLM candidates only on visual/semantic residuals; local semantic-agent candidates only where deterministic/specialized/VLM outputs still require synthesis or interpretation.
- Compare promoted local candidates against contemporaneous authoritative-PDF Codex controls and require provenance-preserving quality equivalence or a clearly bounded assistive role before production use.
- Design the production escalation contract so successful lower-cost tiers suppress unnecessary Codex work, while low-confidence/disagreement cases fall through to Codex and then human review.
- After measured promotion decisions, update localization-matrix.v2 (or create the next measured version), CI-lock the fallback ladder, and run a bounded Lambda integration gate before considering task completion or sustained research.

## Blockers / gates

- The residual taxonomy and promotion gates for OCR, local multimodal/VLM, and local semantic-agent candidates have not yet been formalized or benchmarked.
- The existing benchmark corpus is strong for born-digital scientific text/tables/equations but explicitly lacks sufficient scan/image-only cases; residual fallback validation must add targeted cases rather than reopen the broad parser bakeoff.
- Codex STANDARD EXTRACT/VERIFY remains the semantic production baseline until a cheaper local fallback demonstrates controlled quality/provenance equivalence on the specific residual class it is intended to handle.
- Sustained research remains disabled while residual fallback architecture is being validated.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
