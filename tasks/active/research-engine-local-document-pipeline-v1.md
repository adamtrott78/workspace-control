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
- Remote checkpoint: 1442e787317a94998a60a78d2a2f7582b6192170
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 1442e787317a94998a60a78d2a2f7582b6192170
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead. Do not rerun TableFormer or open another parser yet. Inspect the existing visible output root /home/atrott/adamArchives/Adam/workspace-control-tmp/document-tableformer-accurate-residual-20261003T203427Z. For each JSON file under accurate-pages, print the case/page, len(document['tables']), body/table label counts, and for every table the number of data.table_cells plus any nonempty exported text. Also print the three target-plan entries. Return only that compact diagnostic. If the raw page JSON contains usable table cells, repair/replay evaluation only; if all three target pages contain zero usable table cells, treat TableFormer FAST+ACCURATE as a measured residual and choose a single targeted alternate table fallback.

## Remaining work

- Inspect the three raw TableFormer ACCURATE page outputs under visible workspace-control-tmp and report per-page table item counts, labels, and whether any table data/table_cells exist.
- If ACCURATE emitted table objects with usable cells, fix the evaluator/materialization path and replay evaluation only.
- If ACCURATE emitted zero usable table objects on all three pages, classify TableFormer as unable to close this residual and open one narrowly targeted alternate table fallback rather than a broad parser bakeoff.
- Integrate CodeFormulaV2 as an equation-only escalation path without enabling it globally.
- Advance to local_inference_service_and_concurrency after the table fallback decision so TableFormer/CodeFormula models can remain resident/batched rather than being repeatedly initialized per page.
- Then validate paper-package consumption in EXTRACT/VERIFY and the broader localization matrix.

## Blockers / gates

- Targeted TableFormer ACCURATE did not materialize any of the three empty-grid residual tables. Before selecting another parser family, inspect the raw accurate-page Docling JSON to determine whether the page-bounded invocation emitted zero table objects or emitted table items whose structure was not recognized by the evaluator.
- CodeFormulaV2 passed its quality promotion gate, but production integration remains pending shared-model serving/concurrency work and final deployment/license review.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
