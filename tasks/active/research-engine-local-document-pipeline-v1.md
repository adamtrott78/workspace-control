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

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda, verify the clean research-engine checkout is main@d1dd1d32cf57e9c4423d4d31ef314611ebd4162f, fetch origin, verify canonical commit fbd1508d364ec72a1cb2b3b9013b50a3a3e43286 descends from it, then fast-forward exactly to that commit. Rerun bash deploy/run-document-docling-standard-no-ocr-bakeoff.sh and preserve the complete terminal output plus OUTPUT_ROOT. The helper first runs an unmasked real 256 MiB CUDA allocation control, then probes CUDA_VISIBLE_DEVICES=0 and =1 separately, binds Docling to the first numeric index that passes, and retains GPU UUID only as audit metadata. Do not kill/reset GPU processes, do not fall back to CPU, and keep OCR/formula/VLM/heavier parser tiers disabled.

## Remaining work

- On the stopped Lambda, fast-forward clean research-engine main from d1dd1d32cf57e9c4423d4d31ef314611ebd4162f exactly to fbd1508d364ec72a1cb2b3b9013b50a3a3e43286.
- Rerun bash deploy/run-document-docling-standard-no-ocr-bakeoff.sh and preserve the complete terminal output plus OUTPUT_ROOT.
- Inspect UNMASKED_CUDA_ALLOCATION and both numeric-index allocation probes.
- If a numeric index passes, confirm CUDA_VISIBLE_DEVICES is pinned to that index, SDK self-test passes, and Heron initialization proceeds.
- If the unmasked and both numeric-index probes fail, use the captured environment/device diagnostics to investigate driver/device access next before touching workloads.
- If the corpus benchmark completes, evaluate structure-label recovery, text/order fidelity, throughput, runtime/model footprint and GPU use.

## Blockers / gates

- The Docling standard/no-OCR 73-page benchmark has still not completed; UUID-based CUDA_VISIBLE_DEVICES masks failed initialization on both otherwise-idle/default A4500s.
- The next retry must distinguish UUID-mask incompatibility from a general CUDA allocation problem using the unmasked control and numeric-index probes.
- Do not reset/kill GPU processes or fall back to CPU based on the current evidence.
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
