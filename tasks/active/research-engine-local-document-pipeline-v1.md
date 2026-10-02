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

- Docling native remains validated as the cheap text/order/provenance substrate.
- The standard/no-OCR structure tier direct prefetch now succeeds: layout + TableFormer artifacts were downloaded and measured at 669M.
- The second Lambda retry exposed two runtime requirements before corpus execution: Docling DocumentConverter transitively requires SciPy even with OCR disabled, and PyTorch 2.14.1 CUDA 13.0 is incompatible with the Lambda's NVIDIA 570.133.07 driver.
- research-engine PR #45 is canonical at `f77778587e40a7b65b462cf9fca1d987bab19dbd`; PR CI `36956382368` PASS and canonical-main CI `36956500411` PASS.
- The v3 isolated runtime now uses official PyTorch 2.13.0/TorchVision 0.28.0 CUDA 12.6 plus `docling-slim[convert-core,format-pdf,models-local]==2.131.0` and fails closed unless CUDA is actually available.

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda, verify the clean research-engine checkout is main@350e2d7bffd258248af78d540cc291a78ea83d9b, fetch origin, verify canonical commit f77778587e40a7b65b462cf9fca1d987bab19dbd descends from it, then fast-forward exactly to that commit. Rerun bash deploy/run-document-docling-standard-no-ocr-bakeoff.sh and preserve the complete terminal output plus OUTPUT_ROOT. The helper will recreate the isolated runtime under profile docling-standard-no-ocr-core-cu126-v3, install official PyTorch 2.13.0/TorchVision 0.28.0 CUDA 12.6 wheels, then docling-slim[convert-core,format-pdf,models-local]==2.131.0, directly prefetch layout + TableFormer, and fail closed unless CUDA is available. Keep OCR, formula/code enrichment, VLM, Marker, PaddleOCR, and heavier MinerU tiers disabled.

## Remaining work

- On the stopped Lambda, fast-forward clean research-engine main from 350e2d7bffd258248af78d540cc291a78ea83d9b exactly to f77778587e40a7b65b462cf9fca1d987bab19dbd.
- Rerun bash deploy/run-document-docling-standard-no-ocr-bakeoff.sh and preserve the complete terminal output plus reported OUTPUT_ROOT.
- Confirm runtime recreation under profile docling-standard-no-ocr-core-cu126-v3, SciPy import/version, Torch 2.13.0 CUDA 12.6, torch.cuda.is_available()=True, and resolved RTX A4500 device.
- Confirm DOCLING_STANDARD_NO_OCR_SDK_SELF_TEST=PASS, then evaluate structure-label recovery, text/order fidelity, throughput, runtime/model footprint and GPU use across the same 7-paper / 73-page seed.
- Normalize successful standard_no_ocr JSON to paper-package.v1 and compare semantic headings/tables/figures/captions against native + Mathpix.
- Only if measured gaps remain should formula enrichment, OCR, Marker/Paddle, or other heavier tiers be opened.

## Blockers / gates

- The Docling standard/no-OCR 73-page structure benchmark has not yet completed; the latest attempt stopped at SDK preflight after successful model prefetch.
- The next Lambda retry must prove SciPy import success and CUDA visibility before corpus execution.
- Formula LaTeX recognition and OCR/scanned-document tiers remain intentionally disabled and unvalidated.
- Research daemon must remain inactive/dead throughout the retry.

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
