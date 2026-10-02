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

- Whole-pipeline localization inventory and `paper-package.v1` are canonical.
- Initial benchmark seed: 7 PDF + Mathpix oracle pairs / 73 pages.
- Native baseline: pypdf plain and layout modes, page-grounded and non-materializing.
- Plain preflight mean text/order F1 0.9130/0.8640; layout 0.8848/0.7662.
- research-engine canonical checkpoint: `95cd45877d5b847cad894d964b3374bb79db44f4` with PR and main CI green.

## Next safe action

Keep research-engine-daemon.service inactive/dead and leave Lambda at research-engine main@73697608e3ab179b7ed617b1833796cc47f679c2. Against canonical research-engine main@95cd45877d5b847cad894d964b3374bb79db44f4, implement isolated optional adapter scaffolding for Docling, MinerU, PaddleOCR/PP-StructureV3, and Marker/Surya with fail-closed availability checks, without adding their heavyweight dependencies to the core install or installing model weights on Lambda.

## Remaining work

- Implement isolated optional adapters for Docling, MinerU, PaddleOCR/PP-StructureV3, and Marker/Surya without adding heavy dependencies to the core install.
- Record candidate versions, licenses, install/runtime contracts, and cache/resource expectations.
- Run the seven-paper bakeoff and later add scan-oriented cases before final parser selection.
- Compare structured-content fidelity, provenance, token density, throughput, load cost, and resource use.
- Only then install selected candidate runtimes on Lambda for hardware/concurrency validation.

## Blockers / gates

- Additional scan-oriented cases are still needed before final corpus acceptance.
- Candidate parser runtimes and resource use remain unvalidated.
- No heavyweight document model is installed on Lambda yet; this is intentional.
- Research daemon remains stopped during early benchmark work.

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
