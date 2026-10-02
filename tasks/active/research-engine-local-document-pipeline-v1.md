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

## Current stage

candidate_parser_bakeoff

## Validated so far

- Whole-pipeline localization inventory and `paper-package.v1` contract are validated.
- Seven-paper / 73-page Mathpix seed remains the active benchmark; original PDFs remain authoritative.
- Docling native is validated as the cheap text/order/provenance substrate.
- Docling standard/no-OCR structure bakeoff completed successfully on research-engine `6d7c682b58904829b59d57d2da1a50bee31e2565`.
- Successful standard output is preserved at `/home/atrott/adamArchives/Adam/.workspace-control/tmp/document-docling-standard-no-ocr-20261002T035925Z`; do not rerun it.
- Standard/no-OCR processed 73 pages in 50.461477 s (~1.44665 pages/s), emitted 52,889 tokens vs Mathpix 56,191, and achieved weighted text/read-order agreement about 0.9451/0.9173.
- Structure counts are promising: 24 Docling tables exactly match 24 Mathpix outer table environments; 57 formula items vs 50 Mathpix display equations; 44 picture items with 35 caption-linked vs 34 Mathpix figures.
- Provenance and bbox coverage are 1.0 for every standard case.
- Component decision: native remains the cheap substrate; standard/no-OCR is the leading specialized semantic-structure tier.
- The next gate is content-aware normalization/evaluation, not another parser install.

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. Treat research-engine main@6d7c682b58904829b59d57d2da1a50bee31e2565 and the successful standard_no_ocr OUTPUT_ROOT=/home/atrott/adamArchives/Adam/.workspace-control/tmp/document-docling-standard-no-ocr-20261002T035925Z as the exact baseline. Do not rerun Docling or redownload models. Implement and CI-gate a stopped-daemon normalization/evaluation replay for the preserved standard_no_ocr structured JSONs using the existing DoclingDocument -> paper-package.v1 normalizer. Then run that replay on Lambda and measure provenance coverage plus content-aware table/equation/figure-caption/heading quality against Mathpix and the normalized native packages. Keep formula enrichment, OCR, VLM, Marker, PaddleOCR and heavier MinerU tiers disabled until a specific measured residual gap justifies opening one.

## Remaining work

- Reuse the successful standard_no_ocr OUTPUT_ROOT=/home/atrott/adamArchives/Adam/.workspace-control/tmp/document-docling-standard-no-ocr-20261002T035925Z; do not rerun Docling.
- Generalize or add a stopped-daemon replay helper that feeds each standard_no_ocr structured JSON into the existing DoclingDocument -> paper-package.v1 normalizer.
- Normalize all seven successful standard_no_ocr cases and verify source SHA/page-count, page+bbox provenance, section paths, table assets, equation assets, figure/caption metadata and fail-closed behavior.
- Add content-aware structure metrics: table cell/grid content agreement, equation text/LaTeX usefulness, semantic figure/caption association and heading/section quality. Keep count agreement explicitly separate from content fidelity.
- Compare normalized standard_no_ocr packages directly against normalized native packages and Mathpix references; preserve original PDFs as scientific authority.
- If structure content holds, close candidate_parser_bakeoff and advance to adaptive_page_region_router / structured_elements_and_semantic_escalation with native->standard escalation policy.
- Only open formula enrichment, OCR, Marker/Paddle or heavier MinerU tiers for specific measured residual gaps.

## Blockers / gates

- The successful standard_no_ocr outputs are still RAW_EXTERNAL_OUTPUT; paper-package.v1 normalization/provenance promotion over this exact OUTPUT_ROOT has not yet been run.
- Current structure evidence is primarily label/count agreement. Table cell/grid fidelity, equation-content fidelity, semantic figure/caption association, heading quality and image materialization remain unvalidated.
- Formula enrichment remains intentionally disabled; 57 formula labels vs 50 Mathpix display equations does not establish LaTeX fidelity.
- The standard structure tier is ~4.69x slower than Docling native and has a ~6.8G runtime footprint, so routing policy still matters.
- Research daemon must remain inactive/dead throughout the next normalization/evaluation gate.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's exact next_safe_action.
Keep research-engine-daemon.service inactive/dead unless the capsule explicitly opens a bounded runtime gate.
Mathpix is benchmark/reference only; do not add a paid Mathpix API dependency.
Do not rerun the successful native parsers for the next step; normalize the preserved Docling structured JSONs.
Do not install heavier Docling/Marker/Paddle/MinerU tiers before the structured-native replay is evaluated.
Every fresh-chat initialization or handoff prompt for this task must include the full workspace-control repository URL shown above.
