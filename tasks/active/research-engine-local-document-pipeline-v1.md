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
- Remote checkpoint: f44a20e710f7fb9868eeb2b5a1c654c01f540a48
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 1d461988a9416937a9149e4dd8faeeb666ac0e03
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda cd /home/atrott/adamArchives/Adam/research-engine, require a clean main checkout at f44a20e710f7fb9868eeb2b5a1c654c01f540a48, then start only PostgreSQL with sudo docker compose -f docker-compose.yml up -d db. Wait until sudo docker compose -f docker-compose.yml exec -T db pg_isready -U research_engine -d research_engine succeeds. Re-verify research-engine-daemon.service is inactive/dead PID 0, then rerun bash deploy/run-extract-verify-paper-package-ab.sh. Return the compact zero-model preflight, compact representative semantic A/B, REPRESENTATIVE_AB_DECISION, final safety state, or any ERROR/traceback. Do not start the research daemon, rebuild parser/model runtimes, or start sustained research.

## Remaining work

- With research-engine-daemon.service still inactive/dead, start only the repository PostgreSQL service using sudo docker compose -f docker-compose.yml up -d db and wait until pg_isready reports the research_engine database ready.
- Verify the Lambda research-engine checkout is clean on main at canonical f44a20e710f7fb9868eeb2b5a1c654c01f540a48 (or stop and report if it differs), and verify the daemon remains inactive/dead PID 0.
- Rerun deploy/run-extract-verify-paper-package-ab.sh. The runner must reuse existing native and standard/no-OCR runtimes/model caches and require the zero-model same-page quote/provenance preflight to PASS before semantic calls.
- Evaluate representative low/median/high EXTRACT and VERIFY package arms, exact token/latency reductions, package-context regression signals and any current-PDF controls. Do not equate token savings with plan-allowance savings.
- If the A/B result is quality-safe, validate extract_verify_paper_package_ab and advance to research_pipeline_localization_matrix_validation; otherwise correct context assembly without reopening parser bakeoffs.

## Blockers / gates

- PostgreSQL durable-state service is currently unavailable on Lambda at 127.0.0.1:5432; start only docker-compose.yml service db and verify healthy before rerunning the A/B gate.
- EXTRACT/VERIFY paper-package A/B is CI-gated but not yet measured on the preserved nine-paper Lambda corpus; production replacement remains forbidden until the zero-model and representative semantic results are evaluated.
- CodeFormulaV2 deployment/redistribution obligations still require final license/deployment review before sustained production enablement.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
