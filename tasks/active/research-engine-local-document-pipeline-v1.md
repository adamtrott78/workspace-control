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
- Docling native is validated as the cheap text/order/provenance substrate with 100% page+bbox provenance coverage, but not as the semantic structure layer.
- Real native structured replay exposed zero tables/formulas/section headers/captions and 289 low-level picture objects vs 34 Mathpix semantic figures.
- The bounded specialized structure tier is now canonical at research-engine `2d78451b52e5e5dd667b18118ef4ce5373edf6c6`.
- That tier uses standard Docling layout + TableFormer FAST inference with OCR, formula/code enrichment, picture description/classification, chart extraction, and remote services disabled.
- PR #43 CI `36953847303` PASS and canonical-main CI `36953962450` PASS.
- The next runtime gate measures only this specialized structure tier on the same 73 pages.

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On the Lambda, verify research-engine is clean on main@01797e7a3d0805f02afc7a348125420663623956, fetch origin, verify canonical commit 2d78451b52e5e5dd667b18118ef4ce5373edf6c6 is present and descends from the current checkout, then fast-forward exactly to that commit. Run bash deploy/run-document-docling-standard-no-ocr-bakeoff.sh and preserve the complete terminal output plus reported OUTPUT_ROOT. The helper creates/reuses an isolated standard-no-OCR Docling runtime, prefetches only layout + tableformer artifacts, forces conversion offline after prefetch, reports runtime/model sizes and CUDA visibility, and benchmarks the same 7-paper / 73-page Mathpix seed. Keep OCR, formula/code enrichment, VLM, Marker, PaddleOCR, and heavier MinerU tiers disabled. Keep the daemon inactive/dead throughout.

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
