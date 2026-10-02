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
- Remote checkpoint: db78b236103213c6274e538b1736c4483032c06e
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: db78b236103213c6274e538b1736c4483032c06e
- Local clean: true

## Next safe action

Do not rerun the broad parser bakeoff. Treat candidate_parser_bakeoff as VALIDATED and begin adaptive_page_region_router on research-engine main@db78b236103213c6274e538b1736c4483032c06e. Implement and CI-gate a deterministic hybrid routing/confidence contract with Docling native as the default lexical/order/provenance substrate and standard_no_ocr as a structure overlay. Promote headings/provenance directly; promote only caption-linked pictures as semantic figures; gate tables by content/grid confidence and add a compact residual audit for the Scheirer, Fadul and Broggi failures before selecting any heavier table fallback. In parallel, open one narrowly bounded Docling formula-enrichment experiment for formula-bearing pages/regions because all six equation-bearing seed papers scored equation-content F1=0 without enrichment. Keep OCR, VLM, Marker, PaddleOCR and heavier MinerU disabled unless a measured residual from these targeted gates specifically justifies one. Keep research-engine-daemon.service inactive/dead during benchmark development and do not START sustained research.

## Remaining work

- Implement and CI-gate an adaptive routing contract that preserves Docling native as the default lexical/order/provenance package and applies standard_no_ocr only as a structure overlay under explicit page/region/document signals.
- Add structure-confidence outputs: headings/provenance accepted directly; semantic figures require caption association; tables require cell/grid confidence and fail-closed residual flags.
- Add a compact table-residual audit for the low-scoring Scheirer, Fadul and Broggi cases that exposes candidate/reference cells and LaTeX normalization effects before any heavier table parser is opened.
- Design a bounded Docling formula-enrichment bakeoff only for formula-bearing pages/regions/cases. Keep OCR and VLM disabled; measure equation representation against the same Mathpix reference and original-PDF authority.
- If formula enrichment closes the equation residual, fold it into structured_elements_and_semantic_escalation as an equation-only escalation path rather than enabling it globally.
- Do not reopen Marker, PaddleOCR or heavier MinerU tiers unless the targeted table audit or formula-enrichment experiment leaves a specific residual that Docling cannot close.
- After router and structured-element confidence paths are validated, advance to local_inference_service_and_concurrency and the broader research-pipeline localization matrix.

## Blockers / gates

- Equation representation is not production-usable in standard_no_ocr with formula enrichment disabled: all six equation-bearing seed papers have matched equation-content F1=0 and reference coverage=0.
- Table fidelity is heterogeneous despite exact outer-table counts. Before selecting any heavier table fallback, audit the low-scoring Scheirer, Fadul and Broggi cases to separate evaluator/LaTeX-normalization artifacts from genuine TableFormer cell/grid errors.
- Uncaptioned Docling picture items must not be promoted as semantic figures; only caption-linked pictures are currently validated for semantic figure routing.
- The standard structure tier remains ~4.69x slower than Docling native with a ~6.8G runtime footprint, so production routing must avoid unconditional whole-document structure inference.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
