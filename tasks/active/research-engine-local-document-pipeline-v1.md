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

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda, verify the clean research-engine checkout is main@fbd1508d364ec72a1cb2b3b9013b50a3a3e43286, fetch origin, verify canonical commit b9327a1214bae6bde1d8f7c41f2d35834ef8cf7a descends from it, then fast-forward exactly to that commit. Run bash deploy/diagnose-cuda-host.sh and preserve the complete terminal output. This diagnostic is read-only: it calls libcuda cuInit(0) and cudaGetDeviceCount directly, inspects NVIDIA/UVM modules and device nodes, records kernel command line and recent UVM/Xid/HMM messages, and performs no modprobe, GPU reset, process kill, reboot or kernel-parameter change. Do not rerun Docling until this diagnostic is evaluated.

## Remaining work

- On the stopped Lambda, fast-forward clean research-engine main from fbd1508d364ec72a1cb2b3b9013b50a3a3e43286 exactly to b9327a1214bae6bde1d8f7c41f2d35834ef8cf7a.
- Run bash deploy/diagnose-cuda-host.sh and preserve the complete terminal output.
- Interpret the direct cuInit error code/name/string, CUDA runtime result, nvidia_uvm module/device-node state, permissions, kernel command line and recent UVM/Xid/HMM messages.
- Only after the diagnostic identifies a supported host-level remedy should any module/kernel/reboot action be considered.
- Once direct CUDA initialization passes, return to the standard_no_ocr 73-page structure benchmark.

## Blockers / gates

- The Docling structure benchmark is paused until host-level CUDA initialization succeeds; unmasked CUDA initialization currently fails before any model allocation.
- The root cause may be nvidia_uvm/HMM/device-node/driver initialization; no host mutation is authorized until the read-only diagnostic identifies the failure.
- Do not reset/kill GPUs, reload modules, reboot, alter kernel parameters, or fall back to CPU before reviewing the diagnostic.
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
