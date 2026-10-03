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
- Remote checkpoint: 99fbed6fac76b5feaa67b99625f64acb1f37de39
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: db78b236103213c6274e538b1736c4483032c06e
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda, verify /home/atrott/adamArchives/Adam/research-engine is clean on main@db78b236103213c6274e538b1736c4483032c06e, fetch origin/main, require origin/main=99fbed6fac76b5feaa67b99625f64acb1f37de39, and fast-forward only to that exact commit. Then run bash deploy/run-document-hybrid-routing-followup.sh with no arguments. The runner must reuse the preserved standard_no_ocr and normalized-native packages, execute the oracle-free hybrid routing report and compact table residual audit, derive formula-bearing target pages from preserved standard provenance, prefetch the pinned CodeFormulaV2 revision only into the isolated formula benchmark cache, run formula enrichment one page at a time only for those targets, and evaluate equation content against Mathpix as benchmark reference with the original PDF authoritative. Return only the compact terminal summary and any ERROR line. Do not rerun the 73-page standard parser bakeoff and do not enable OCR, broad document VLM, Marker, PaddleOCR or heavier MinerU.

## Remaining work

- Fast-forward the clean Lambda research-engine main checkout from db78b236103213c6274e538b1736c4483032c06e to canonical 99fbed6fac76b5feaa67b99625f64acb1f37de39 while the daemon remains inactive/dead.
- Run deploy/run-document-hybrid-routing-followup.sh once. It must reuse preserved native/standard packages for routing and table audit, derive formula target pages from preserved standard_no_ocr provenance, and run CodeFormulaV2 only on those pages.
- Review the compact table residual audit to separate evaluator/LaTeX normalization artifacts from genuine cell/grid failures before opening any heavier table fallback.
- Evaluate targeted CodeFormulaV2 against the same Mathpix reference and original-PDF authority. Promote it only if the explicit formula content/coverage gate is met; otherwise characterize the remaining residual.
- If formula enrichment passes, integrate it as an equation-only escalation path in structured_elements_and_semantic_escalation rather than enabling it globally.
- Do not reopen Marker, PaddleOCR or heavier MinerU tiers unless the targeted table/formula results leave a specific measured residual that requires one.
- After the Lambda routing/structure gate is validated, advance to local_inference_service_and_concurrency and then the broader research-pipeline localization validation.

## Blockers / gates

- Lambda local research-engine is last verified at clean main@db78b236103213c6274e538b1736c4483032c06e while canonical remote main is 99fbed6fac76b5feaa67b99625f64acb1f37de39. Fast-forward locally before running the combined gate.
- Table residual classification is implemented but the real Scheirer/Fadul/Broggi diagnostic output has not yet been executed on Lambda; do not choose a heavier table parser until that audit is reviewed.
- Targeted CodeFormulaV2 is implemented and CI-gated but has not yet been executed on the Lambda seed. Equation promotion remains blocked until measured content F1/coverage pass the explicit gate.
- The new CodeFormulaV2 weights are intentionally not yet present in the production path. Benchmark fetch is justified by the measured equation residual; production promotion still requires benchmark quality plus license/deployment review.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
