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

## Research-engine checkpoints

- Canonical remote main: 94cd8366d6a78f35b18286cbf14f9c49af420d90
- Lambda/local recorded HEAD: 73697608e3ab179b7ed617b1833796cc47f679c2
- Lambda/local clean: true

## Validated so far

- `paper-package.v1` and whole-pipeline localization matrix.
- Seven-paper / 73-page Mathpix seed and native pypdf baselines.
- Isolated version/license/runtime contracts for Docling, MinerU, PaddleOCR/PP-StructureV3, and Marker.
- External parser subprocesses are local-only, version-checked, shell-free, and cannot claim `paper-package.v1` provenance until a parser-specific normalizer is validated.
- First runtime gate is deliberately limited to lightweight Docling native + MinerU flash-native.

## Next safe action

Keep research-engine-daemon.service inactive/dead. On the Lambda, verify the clean research-engine checkout is main@73697608e3ab179b7ed617b1833796cc47f679c2 and fast-forward only to canonical main@94cd8366d6a78f35b18286cbf14f9c49af420d90. Under $HOME/adamArchives/Adam/.document-runtimes, create isolated Docling and MinerU virtual environments. Install only docling-slim[cli,format-pdf]==2.131.0 and mineru>=4.0,<5, set RESEARCH_ENGINE_DOCLING_BIN and RESEARCH_ENGINE_MINERU_BIN to those isolated executables, run research-engine document-adapter-status, then benchmark docling/native and mineru/flash_native over benchmarks/document_intelligence/cases/milcom-mathpix-seed-v1.json using the PADataset reference_notes directory as bundle root and a workspace-control tmp directory as output. Record venv/cache disk usage and complete benchmark output. Do not install Marker, PaddleOCR, Torch/full MinerU, VLM weights, or START sustained research.

## Remaining work

- On the stopped Lambda, fast-forward research-engine main from 73697608e3ab179b7ed617b1833796cc47f679c2 to canonical 94cd8366d6a78f35b18286cbf14f9c49af420d90.
- Create isolated Docling and MinerU virtual environments under AdamArchives without modifying the core research-engine venv.
- Install only Docling slim native-PDF profile and MinerU base profile; capture venv/cache disk usage before and after.
- Run document-adapter-status, then the seven-paper Docling native and MinerU flash-native external benchmarks against the existing PADataset PDFs/Mathpix oracles.
- If either runtime command fails, stop and patch the exact command/version contract before retrying; do not fall through to remote services.
- Compare the two fast paths against native-pypdf and Mathpix before deciding whether to test specialized or VLM tiers.
- Later add scanned/malformed-text cases, structured-output provenance normalizers, and selected heavy-runtime/concurrency tests.

## Blockers / gates

- Docling-native and MinerU flash-native command/runtime contracts are CI-validated but have not yet been exercised against the actual Lambda environments.
- Additional scanned/broken-text-layer cases remain necessary before final corpus acceptance.
- Specialized/VLM tiers, Marker, PaddleOCR, model weights, GPU/VRAM use, and multi-document concurrency remain unvalidated.
- Research daemon must remain inactive/dead throughout the bounded parser-runtime experiment.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal `workspace-control` root route.
Treat the authoritative capsule, synchronized Markdown handoff, exact durable Git/runtime state, and referenced research-engine evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's exact `next_safe_action`.
Keep `research-engine-daemon.service` inactive/dead unless the capsule explicitly opens a different bounded runtime gate.
Mathpix outputs are benchmark/reference artifacts only; do not add a paid Mathpix API dependency.
Do not install Marker, PaddleOCR, Torch/full MinerU, VLM weights, or START sustained research during the current cheap-parser runtime gate.
Every fresh-chat initialization or handoff prompt for this task must include the full workspace-control repository URL shown above.
