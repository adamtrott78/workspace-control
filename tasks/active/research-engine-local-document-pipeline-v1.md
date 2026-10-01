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

benchmark_corpus_and_mathpix_oracle

## Validated so far

- Whole-pipeline localization inventory: 27 components classified across deterministic local, specialized local model, on-demand local VLM, external web, remote reasoning, and human.
- `paper-package.v1`: canonical executable contract with deterministic cache identity and page/bbox/section provenance.
- Benchmark exchange convention: small Markdown/JSON parser and Mathpix oracle outputs may use GitHub; bulky PDFs/model weights stay out of Git.
- research-engine canonical checkpoint: `ac49579badbef02694a6f8b08061c50570704aee` with PR and canonical-main CI green.

## Next safe action

Keep research-engine-daemon.service inactive/dead. Do not install heavyweight OCR/VLM models on the Lambda yet. Build the benchmark corpus/oracle layer next against canonical research-engine main@ac49579badbef02694a6f8b08061c50570704aee: add benchmark case/oracle manifests plus a non-materializing runner, implement the deterministic native-PDF adapter as the baseline, and prepare adapter wrappers that keep Docling/MinerU/PaddleOCR/Marker optional and isolated. The user can meanwhile generate Mathpix Markdown/image bundles manually and provide or push them under the documented benchmark convention. Begin candidate model installation only after representative cases exist.

## Remaining work

- Assemble a compact representative benchmark corpus: preserved research-engine papers plus deliberately difficult pages for two-column order, malformed text, scans, equations, tables, charts/figures, mixed layouts, and references.
- User may manually generate Mathpix Markdown/image bundles for chosen cases using the desktop annual allowance and provide them in chat or push small outputs under benchmarks/document_intelligence/oracles/<case-id>/.
- Add case/oracle manifests and a benchmark runner that validates source hashes and scores adapter outputs without mutating scientific state.
- Implement native PDF adapter first as deterministic baseline, then add isolated adapters for Docling, MinerU, PaddleOCR/PP-StructureV3, and Marker/Surya without forcing all dependencies into the core production install.
- Measure document fidelity, provenance, token density, pages/sec, memory/VRAM, model-load cost, and concurrent throughput before selecting component winners.
- Only after desktop/CI bakeoff should selected local models be installed and benchmarked on the Lambda.
- Then continue adaptive routing, structured scientific element handling, whole-pipeline localization decisions, and downstream EXTRACT/VERIFY A/B.

## Blockers / gates

- Representative benchmark cases and manual Mathpix oracle bundles have not yet been assembled.
- Candidate parser/model licensing and Lambda VRAM/RAM/throughput remain unvalidated.
- No heavyweight local document model has been selected or installed; this is intentional until benchmark cases exist.
- Research-engine Lambda checkout remains at 73697608e3ab179b7ed617b1833796cc47f679c2 and does not need to fast-forward for corpus/oracle assembly.
- The research daemon must remain stopped during early benchmark/integration work.

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
Every fresh-chat initialization or handoff prompt for this task must include the full workspace-control repository URL shown above.
