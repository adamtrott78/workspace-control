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

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 134d60630a1bf16499fee169f28456a670de343f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: db78b236103213c6274e538b1736c4483032c06e
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 6d7c682b58904829b59d57d2da1a50bee31e2565
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. Treat canonical research-engine remote main@db78b236103213c6274e538b1736c4483032c06e as the validated replay implementation and Lambda local main@6d7c682b58904829b59d57d2da1a50bee31e2565 as the last verified local state. On Lambda, first verify the checkout is clean and the daemon is inactive/dead, then fast-forward local main to db78b236103213c6274e538b1736c4483032c06e. Identify the already-existing normalized Docling-native paper-package root without rerunning Docling/native. Then run deploy/run-docling-standard-structure-replay.sh with the preserved standard_no_ocr OUTPUT_ROOT=/home/atrott/adamArchives/Adam/.workspace-control/tmp/document-docling-standard-no-ocr-20261002T035925Z and that normalized-native root. Return the terminal summary and docling-normalization-summary.json for evaluation. Do not rerun parser inference, redownload models, or enable formula enrichment, OCR, VLM, Marker, PaddleOCR or heavier MinerU tiers before a measured residual gap justifies one.

## Remaining work

- With research-engine-daemon.service inactive/dead, verify the Lambda checkout is clean and fast-forward local research-engine main from 6d7c682b58904829b59d57d2da1a50bee31e2565 to canonical remote main@db78b236103213c6274e538b1736c4483032c06e.
- Locate the already-existing normalized Docling-native paper-package.v1 root on Lambda; do not rerun the native parser or the 73-page benchmark.
- Run deploy/run-docling-standard-structure-replay.sh against /home/atrott/adamArchives/Adam/.workspace-control/tmp/document-docling-standard-no-ocr-20261002T035925Z and the existing normalized-native root. This replay must not invoke Docling inference or model downloads.
- Inspect docling-standard-no-ocr-paper-package-v1/docling-normalization-summary.json for provenance coverage and content-aware table cell/grid, equation, figure-caption, heading/section metrics plus standard-minus-native deltas.
- If structure content holds, close candidate_parser_bakeoff and advance to adaptive_page_region_router / structured_elements_and_semantic_escalation with native->standard escalation policy.
- Only open formula enrichment, OCR, Marker/PaddleOCR or heavier MinerU tiers for a specific measured residual gap.

## Blockers / gates

- Lambda local research-engine is last verified clean at 6d7c682b58904829b59d57d2da1a50bee31e2565 while canonical remote main is db78b236103213c6274e538b1736c4483032c06e; fast-forward the stopped-daemon local checkout before replay.
- The exact Lambda-local root of the already-normalized Docling-native paper-package.v1 corpus is not recorded in durable state. Identify the existing root locally and pass it to the replay; do not rerun Docling/native to recreate the benchmark.
- The preserved standard_no_ocr structured JSON has not yet been normalized/evaluated with the merged content-aware gate, so table/equation/figure-caption/heading content fidelity remains unknown.
- Formula enrichment remains intentionally disabled; only a measured equation-content residual from this replay may justify opening it.
- The standard structure tier remains ~4.69x slower than Docling native with a ~6.8G runtime footprint, so routing policy still matters.
- research-engine-daemon.service must remain inactive/dead throughout the Lambda normalization/evaluation replay.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
