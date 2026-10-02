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

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda, verify the clean research-engine checkout is main@b9327a1214bae6bde1d8f7c41f2d35834ef8cf7a, fetch origin, verify canonical commit 6d7c682b58904829b59d57d2da1a50bee31e2565 descends from it, then fast-forward exactly to that commit. Rerun bash deploy/run-document-docling-standard-no-ocr-bakeoff.sh and preserve the complete terminal output plus OUTPUT_ROOT. The runner will migrate the existing healthy v3 structure runtime in place to profile docling-standard-no-ocr-core-cu126-opencv-v4 by installing only the official docling-ibm-models[opencv-python-headless] extra, then verify cv2 and TableFormer TFPredictor imports before model prefetch and corpus execution. Do not rebuild the full runtime unless the profile is unexpected. Keep OCR/formula/VLM/heavier parser tiers disabled and keep the daemon inactive/dead.

## Remaining work

- On the stopped Lambda, fast-forward clean research-engine main from b9327a1214bae6bde1d8f7c41f2d35834ef8cf7a exactly to 6d7c682b58904829b59d57d2da1a50bee31e2565.
- Rerun bash deploy/run-document-docling-standard-no-ocr-bakeoff.sh and preserve the complete terminal output plus OUTPUT_ROOT.
- Confirm MIGRATE_RUNTIME_PROFILE=v3->v4, OPENCV_VERSION, TABLEFORMER_IMPORT_PREFLIGHT=PASS, GPU allocation, SDK self-test and Heron/TableFormer initialization all succeed.
- If the 7-paper / 73-page benchmark completes, evaluate structure-label recovery, text/order fidelity, throughput, runtime/model footprint and GPU use.
- Normalize successful standard_no_ocr structured JSON into paper-package.v1 and compare semantic headings/tables/figures/captions against native + Mathpix.
- Only if measured gaps remain should formula enrichment, OCR, Marker/Paddle, or other heavier tiers be opened.

## Blockers / gates

- The Docling standard/no-OCR 73-page structure benchmark still has not completed; the current blocker is the now-corrected optional OpenCV backend for TableFormer.
- The next retry must pass TABLEFORMER_IMPORT_PREFLIGHT before corpus execution.
- Formula enrichment, OCR, VLM, Marker/Paddle, and heavier MinerU tiers remain disabled.
- Research daemon must remain inactive/dead.

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
