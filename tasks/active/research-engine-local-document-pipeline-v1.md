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

localization_inventory_and_benchmark_contract

## Architectural direction

- Build a content-addressed `paper-package.v1` rather than coupling downstream research to Mathpix or any one local converter.
- Use deterministic/native PDF processing first, specialized local document models second, and a general local VLM only as an escalation path.
- Treat the original PDF as scientific authority; Markdown/JSON/tables/figure descriptions remain derived artifacts with page/region provenance.
- Use manually generated Mathpix Markdown as a benchmark oracle without introducing paid Mathpix API calls into production.
- Benchmark sustained multi-document throughput and a shared inference service, not just single-PDF latency.
- Evaluate localization across the whole research pipeline once: document parsing, caching/chunking, embeddings/retrieval, SCREEN/EXTRACT/VERIFY, and explicit retain-remote decisions for web-dependent/high-level reasoning.

## Benchmark candidates

- Native PDF text/layout/image extraction and deterministic OCR fallbacks
- Docling
- MinerU
- PaddleOCR / PP-StructureV3
- Marker / Surya
- Component-level hybrids selected from benchmark evidence

## Next safe action

Keep research-engine-daemon.service inactive/dead. On a new isolated research-engine branch from canonical main@73697608e3ab179b7ed617b1833796cc47f679c2, implement only the benchmark scaffolding and paper-package.v1 contract first: define the package manifest/provenance/diagnostics schemas, benchmark manifest/result schema, and adapter interface for native/Docling/MinerU/PaddleOCR/Marker candidates. Do not install heavyweight models on the Lambda yet and do not replace EXTRACT/VERIFY. In parallel, the user may generate Mathpix Markdown/image bundles manually and provide or push them as benchmark oracle outputs.

## Remaining work

- Complete the full localization matrix for research-engine stages and subcomponents, explicitly separating deterministic/local-model/external-web/remote-strong-reasoning responsibilities.
- Define paper-package.v1 and benchmark metrics before selecting a converter.
- Create a benchmark result layout in research-engine that can receive local parser outputs and user-generated Mathpix Markdown without committing large source PDFs or model weights.
- Assemble representative test papers/pages, including preserved research-engine papers and difficult scientific layouts; accept Mathpix outputs from the user as reference artifacts.
- Build adapters and benchmark native extraction, Docling, MinerU, PaddleOCR/PP-StructureV3, Marker/Surya, and justified component variants.
- Select/build the adaptive page/region router and shared inference architecture based on measurements.
- Integrate structured tables/equations/figures with provenance and on-demand visual semantic escalation.
- Run downstream EXTRACT/VERIFY A/B and Lambda concurrency/resource acceptance before any production replacement.

## Blockers / gates

- No benchmark corpus/Mathpix oracle bundle has yet been assembled for this task.
- paper-package.v1 and objective acceptance thresholds are not yet finalized.
- Candidate model licensing, Lambda VRAM/RAM requirements, and sustained multi-document throughput are not yet validated.
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
