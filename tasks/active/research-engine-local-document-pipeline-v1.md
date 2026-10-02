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
- `deploy/run-document-native-fast-bakeoff.sh` is canonical at research-engine `3729fadcc371e0a0d2b938a9e8b5842a134604f0`; PR and canonical-main CI are green.

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On the Lambda, verify the research-engine checkout is clean on main@73697608e3ab179b7ed617b1833796cc47f679c2, fetch origin, verify canonical commit 3729fadcc371e0a0d2b938a9e8b5842a134604f0 is present and descends from the current checkout, then fast-forward exactly to that commit. Run bash deploy/run-document-native-fast-bakeoff.sh and preserve the complete terminal output plus the reported OUTPUT_ROOT. The helper will create isolated Docling-native and MinerU-base environments, install only the pinned lightweight profiles, run document-adapter-status, benchmark docling/native and mineru/flash_native over the 7-paper/73-page seed, record disk/cache footprint, and finish with the daemon inactive/dead. Do not install Marker, PaddleOCR, Torch/full MinerU, Docling standard/VLM, or any other heavier model tier yet.

## Remaining work

- On the stopped Lambda, fast-forward the clean research-engine main checkout from 73697608e3ab179b7ed617b1833796cc47f679c2 exactly to 3729fadcc371e0a0d2b938a9e8b5842a134604f0.
- Run bash deploy/run-document-native-fast-bakeoff.sh and preserve the full terminal output plus its reported OUTPUT_ROOT.
- Compare Lambda Docling-native and MinerU-flash-native fidelity, reading order, throughput, runtime footprint, and cache footprint against native-pypdf and Mathpix.
- If either lightweight runtime command/install fails, patch only the exact runtime contract and rerun; do not fall through to remote APIs or heavier parser tiers.
- Only after the cheap paths are measured decide whether to install/run Docling standard, MinerU basic/standard, Marker, or PaddleOCR.
- Later add scanned/malformed-text cases, parser-specific provenance normalizers, structured-content fidelity metrics, and selected heavy-runtime/concurrency tests.

## Blockers / gates

- Docling-native and MinerU flash-native are canonical and CI-validated but have not yet been exercised on the Lambda hardware/runtime.
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
