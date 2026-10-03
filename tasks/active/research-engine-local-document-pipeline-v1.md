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
- Remote checkpoint: a83850016efe2e58b37a86a4203d69af811117a1
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: f44a20e710f7fb9868eeb2b5a1c654c01f540a48
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda cd /home/atrott/adamArchives/Adam/research-engine, require a clean main checkout at f44a20e710f7fb9868eeb2b5a1c654c01f540a48, fetch origin/main, require origin/main=a83850016efe2e58b37a86a4203d69af811117a1, and fast-forward only to that commit. Keep the PostgreSQL db service running/healthy and verify the research daemon remains inactive/dead PID 0. Then run bash deploy/resume-extract-verify-paper-package-ab.sh /home/atrott/adamArchives/Adam/workspace-control-tmp/extract-verify-paper-package-ab-20261003T223020Z. The resume gate must reuse the already-normalized 9 native + 9 standard packages, invoke no Docling compilation/normalization/model download, require the zero-model preflight to PASS before semantic calls, then run representative semantic A/B with current-PDF controls only after package disagreement. Return the compact zero-model preflight, compact representative semantic A/B, REPRESENTATIVE_AB_DECISION, final safety state, or any ERROR/traceback.

## Remaining work

- Fast-forward the clean Lambda research-engine checkout from f44a20e710f7fb9868eeb2b5a1c654c01f540a48 to canonical a83850016efe2e58b37a86a4203d69af811117a1 while research-engine-daemon.service remains inactive/dead.
- Resume from /home/atrott/adamArchives/Adam/workspace-control-tmp/extract-verify-paper-package-ab-20261003T223020Z using deploy/resume-extract-verify-paper-package-ab.sh. Do not rerun either Docling batch compiler or normalization; the resume gate requires exactly 9 native and 9 standard normalized packages.
- Require the zero-model same-page quote/provenance preflight to PASS before semantic replay, then evaluate low/median/high EXTRACT and VERIFY package arms plus disagreement-triggered current-PDF controls.
- Evaluate exact token/latency reductions and package-context regression signals without equating token savings to plan-allowance savings.
- If quality-safe, validate extract_verify_paper_package_ab and advance to research_pipeline_localization_matrix_validation; otherwise correct context assembly without reopening parser bakeoffs.

## Blockers / gates

- Lambda local research-engine is last verified clean at main@f44a20e710f7fb9868eeb2b5a1c654c01f540a48 while canonical remote main is a83850016efe2e58b37a86a4203d69af811117a1; fast-forward before resuming the A/B gate.
- Zero-model preflight and representative semantic A/B have not yet completed; production paper-package replacement remains forbidden until measured.
- CodeFormulaV2 deployment/redistribution obligations still require final license/deployment review before sustained production enablement.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
