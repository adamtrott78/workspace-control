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

- Whole-pipeline localization inventory and `paper-package.v1` are validated.
- Seven-paper / 73-page Mathpix seed and native pypdf baseline are canonical.
- Isolated adapter/runtime contracts for Docling, MinerU, PaddleOCR/PP-StructureV3, and Marker are canonical.
- Cheap runtime gate is open only for Docling `native` and MinerU `flash_native`.
- `deploy/run-document-native-fast-bakeoff.sh` is canonical at research-engine `9e343436ccda56c08936855b48079302f7470e0a`. Docling/native now bypasses the CLI and executes through the model-free SDK shim after the third Lambda attempt proved the CLI initializes unrelated OCR/VLM plugins.

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On the Lambda, verify the research-engine checkout is clean on main@4f64fd63e3586ef9685e63e7a090827df07c2f3b, fetch origin, verify canonical commit 9e343436ccda56c08936855b48079302f7470e0a is present and descends from the current checkout, then fast-forward exactly to that commit. Rerun bash deploy/run-document-native-fast-bakeoff.sh and preserve the complete terminal output plus reported OUTPUT_ROOT. The helper will reuse the existing isolated Docling/MinerU venvs, preflight benchmarks/document_intelligence/runtimes/docling_native.py with --self-test, execute docling/native through the model-free Python SDK shim rather than the CLI, then run mineru/flash_native. Do not install Marker, PaddleOCR, Torch/full MinerU, Docling standard/VLM, or any other heavier tier yet.

## Remaining work

- On the stopped Lambda, verify research-engine is clean on main@4f64fd63e3586ef9685e63e7a090827df07c2f3b and fast-forward exactly to 9e343436ccda56c08936855b48079302f7470e0a.
- Rerun bash deploy/run-document-native-fast-bakeoff.sh and preserve the complete terminal output plus reported OUTPUT_ROOT.
- Confirm DOCLING_NATIVE_SDK_SELF_TEST=PASS before accepting Docling benchmark execution.
- Compare Lambda Docling-native SDK and MinerU-flash-native fidelity, reading order, throughput, runtime footprint, and cache footprint against native-pypdf and Mathpix.
- If the SDK shim itself now fails, patch only that exact model-free runtime boundary; do not re-route native mode back through the CLI and do not fall through to heavier tiers.
- Only after the cheap paths are measured decide whether to install/run Docling standard, MinerU basic/standard, Marker, or PaddleOCR.

## Blockers / gates

- Docling-native and MinerU flash-native still have not completed the Lambda benchmark because Docling's CLI initialization stopped the third attempt before conversion; the native path now bypasses the CLI.
- Additional scanned/broken-text-layer cases remain necessary before final corpus acceptance.
- Specialized/VLM tiers, Marker, PaddleOCR, model weights, GPU/VRAM use, and multi-document concurrency remain unvalidated.
- Research daemon must remain inactive/dead throughout the bounded parser-runtime experiment.

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
Mathpix outputs supplied by the user are benchmark/reference artifacts only; do not add a paid Mathpix API dependency.
Do not install Marker, PaddleOCR, Torch/full MinerU, Docling standard/VLM, or other heavy tiers before the cheap Docling-native/MinerU-flash bakeoff is evaluated.
Every fresh-chat initialization or handoff prompt for this task must include the full workspace-control repository URL shown above.
