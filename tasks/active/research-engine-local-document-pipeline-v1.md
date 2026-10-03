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
- Local HEAD: 99fbed6fac76b5feaa67b99625f64acb1f37de39
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead. On Lambda, verify /home/atrott/adamArchives/Adam/research-engine is clean on main@99fbed6fac76b5feaa67b99625f64acb1f37de39, fetch origin/main, require origin/main=1442e787317a94998a60a78d2a2f7582b6192170, and fast-forward only to that exact commit. Then run bash deploy/run-tableformer-accurate-residual-gate.sh. The gate must reuse the existing Docling 2.131.0 standard runtime/model cache, select only the three FAST-mode table assets whose normalized grids are empty, run TableFormerMode.ACCURATE one page at a time only on those targets, keep OCR/formula/picture/general-VLM/remote-service paths disabled, and write all new artifacts beneath visible ~/adamArchives/Adam/workspace-control-tmp/. Return the compact TABLEFORMER ACCURATE summary and any ERROR line. Do not rerun the 73-page parser bakeoff and do not open another table parser family until this targeted residual is measured.

## Remaining work

- Fast-forward the clean Lambda research-engine checkout from 99fbed6fac76b5feaa67b99625f64acb1f37de39 to canonical 1442e787317a94998a60a78d2a2f7582b6192170 while the daemon remains inactive/dead.
- Run deploy/run-tableformer-accurate-residual-gate.sh once. It must select only the 3 intrinsic empty-grid FAST residuals, reuse the existing Docling/TableFormer runtime and cache, and execute ACCURATE mode only on the selected pages.
- Review the compact TableFormer ACCURATE evaluation. If the three tables recover above the promotion gate, integrate ACCURATE as an empty-grid-only table escalation; otherwise characterize the remaining table residual before considering any other parser family.
- Integrate CodeFormulaV2 as an equation-only escalation path without enabling it globally.
- Advance to local_inference_service_and_concurrency so TableFormer/CodeFormula models can remain resident/batched rather than being repeatedly initialized per page.
- Then validate paper-package consumption in EXTRACT/VERIFY and the broader localization matrix; do not reopen Marker/PaddleOCR/heavier MinerU without a specific measured residual.

## Blockers / gates

- Lambda local research-engine is verified at clean main@99fbed6fac76b5feaa67b99625f64acb1f37de39 while canonical remote main is 1442e787317a94998a60a78d2a2f7582b6192170; fast-forward locally before the targeted TableFormer ACCURATE gate.
- The three intrinsic FAST-mode empty-grid table failures (2 Scheirer, 1 Fadul) still require the bounded TableFormer ACCURATE Lambda measurement before table escalation policy is final.
- CodeFormulaV2 passed its quality promotion gate, but production integration remains pending shared-model serving/concurrency work and final deployment/license review.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
