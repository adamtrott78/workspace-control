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

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda, verify the clean research-engine checkout is main@f77778587e40a7b65b462cf9fca1d987bab19dbd, fetch origin, verify canonical commit d1dd1d32cf57e9c4423d4d31ef314611ebd4162f descends from it, then fast-forward exactly to that commit. Rerun bash deploy/run-document-docling-standard-no-ocr-bakeoff.sh and preserve the complete terminal output plus OUTPUT_ROOT. The helper will inventory every GPU, report active compute processes, probe each GPU with a real 256 MiB CUDA allocation/write/synchronize, bind the first healthy device by GPU UUID using CUDA_VISIBLE_DEVICES, force Docling device=cuda, and fail closed if none pass. Do not kill/reset GPU processes, do not fall back to CPU, and keep OCR/formula/VLM/heavier parser tiers disabled.

## Remaining work

- On the stopped Lambda, fast-forward clean research-engine main from f77778587e40a7b65b462cf9fca1d987bab19dbd exactly to d1dd1d32cf57e9c4423d4d31ef314611ebd4162f.
- Rerun bash deploy/run-document-docling-standard-no-ocr-bakeoff.sh and preserve the complete terminal output plus reported OUTPUT_ROOT.
- Inspect GPU inventory, compute mode, active compute processes and the per-GPU 256 MiB allocation probes.
- Confirm a SELECTED_PHYSICAL_GPU_UUID is emitted, CUDA_VISIBLE_DEVICES is pinned to it, SDK self-test passes and Heron model initialization proceeds.
- If the benchmark completes, evaluate structure-label recovery, text/order fidelity, throughput, runtime/model footprint and GPU use across the same 7-paper / 73-page seed.
- If all GPUs fail allocation, diagnose occupancy/compute-mode state from the captured output before taking any action that could affect other workloads.

## Blockers / gates

- The Docling standard/no-OCR 73-page structure benchmark still has not completed because actual Heron GPU allocation failed on the device selected by AUTO.
- The next retry must establish whether at least one physical A4500 passes a real CUDA allocation probe and, if so, pin Docling to that device.
- If no GPU passes the probe, the preserved GPU inventory/compute-process output must be evaluated before any reset, kill, or CPU fallback is considered.
- Formula enrichment, OCR, VLM, Marker/Paddle, and heavier MinerU tiers remain disabled.
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
