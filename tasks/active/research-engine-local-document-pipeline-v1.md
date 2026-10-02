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
- Seven-paper / 73-page Mathpix seed is active; original PDFs remain authoritative.
- Docling native cheap path completed successfully and remains the leading text/order/provenance substrate.
- Real structured replay completed at research-engine `01797e7a3d0805f02afc7a348125420663623956`: 100% page provenance and bbox coverage across all normalized body items.
- Normalized text remained strong: 55,482 tokens vs Mathpix 56,191 with weighted text/read-order agreement about 0.930/0.891.
- Native semantic structure is insufficient: zero tables, formulas, section headers and caption items across the seed; 289 native picture objects correspond to only 34 Mathpix semantic figures.
- Therefore native `picture` items are not to be materialized as semantic figures. The next tier is specialized structure augmentation.
- MinerU `flash_native` remains rejected only in its current configuration.

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. Implement and CI-gate a Docling standard/no-OCR SDK structure benchmark from canonical research-engine main@01797e7a3d0805f02afc7a348125420663623956. Configure PdfPipelineOptions with do_ocr=false, do_table_structure=true, do_code_enrichment=false, do_formula_enrichment=false, generate_page_images=false, generate_picture_images=false and enable_remote_services=false; use an isolated runtime and explicit local model-artifact cache. Do not enable the Docling VLM pipeline, formula enrichment, OCR, Marker, PaddleOCR, or heavier MinerU tiers yet. After merge, run the stopped-daemon standard/no-OCR benchmark on the same seven-paper / 73-page Mathpix seed and preserve complete terminal output plus model/runtime size metrics.

## Remaining work

- Implement an isolated Docling standard SDK shim that runs layout + table-structure inference with OCR disabled, formula/code enrichment disabled, picture description/classification disabled, page/picture image generation disabled and remote services disabled.
- Keep the specialized structure runtime isolated from the 421M native Docling environment; record exact runtime size, model-artifact cache size and model versions.
- Benchmark the standard/no-OCR structure tier against the same seven-paper / 73-page corpus while the daemon is stopped.
- Normalize standard Docling JSON with the existing paper-package.v1 normalizer and compare headings, tables, formulas, semantic figures/captions, provenance, text/order fidelity, wall time and output volume to native + Mathpix.
- Only if standard/no-OCR fails formula content should formula enrichment be benchmarked as a separate targeted escalation; do not enable it globally by default.
- Run pypdf plain on the same Lambda for controlled throughput/resource comparison.
- After structure augmentation is characterized, run non-materializing EXTRACT/VERIFY A/B using paper-package.v1 before production integration.
- Benchmark Marker/Paddle/MinerU heavier tiers only if Docling specialized structure cannot satisfy specific measured gaps.

## Blockers / gates

- Docling native is validated only as a text/order/provenance substrate; it does not provide usable semantic table/formula/heading/caption classification on this corpus.
- Native Docling picture items must not be treated as semantic figures; 289 native picture items correspond to only 34 Mathpix figures across the seed.
- A specialized local structure tier is now required for layout/heading/table/figure classification; formula LaTeX recognition remains a separate later escalation.
- A same-Lambda pypdf plain benchmark is still needed before direct pypdf-vs-Docling native throughput comparison.
- Scanned/malformed-text cases and OCR tiers remain unvalidated.
- Research daemon must remain inactive/dead throughout specialized structure-tier benchmarking.

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
