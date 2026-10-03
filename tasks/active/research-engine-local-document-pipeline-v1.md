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

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda verify /home/atrott/adamArchives/Adam/research-engine is clean on main@1d461988a9416937a9149e4dd8faeeb666ac0e03, fetch origin/main, require origin/main=f44a20e710f7fb9868eeb2b5a1c654c01f540a48, and fast-forward only to that exact commit. Then run bash deploy/run-extract-verify-paper-package-ab.sh. The gate must reuse the existing Docling native and standard/no-OCR runtimes/model cache without environment/model rebuilds, compile the preserved nine source artifacts, require the zero-model same-page quote/provenance preflight to PASS before any semantic replay, then run the representative low/median/high EXTRACT and VERIFY package arms with current-PDF controls only after package disagreement. Scientific state must not be materialized; only operational calibration events may be recorded. Keep the daemon inactive/dead throughout and return the compact zero-model preflight, compact representative semantic A/B, REPRESENTATIVE_AB_DECISION, final safety state, or any ERROR line.

## Remaining work

- Fast-forward the clean Lambda research-engine checkout from 1d461988a9416937a9149e4dd8faeeb666ac0e03 to canonical f44a20e710f7fb9868eeb2b5a1c654c01f540a48 while the daemon remains inactive/dead.
- Run deploy/run-extract-verify-paper-package-ab.sh once. The runner first compiles the nine preserved source artifacts with the existing native and standard/no-OCR runtimes, then requires the zero-model same-page quote/provenance preflight to PASS before semantic calls.
- Evaluate the representative low/median/high EXTRACT and VERIFY package arms, exact token/latency reductions, package-context regression signals and any current-PDF controls. Do not equate token savings with plan-allowance savings.
- If the A/B result is quality-safe, validate extract_verify_paper_package_ab and advance to research_pipeline_localization_matrix_validation. If a package-only regression appears, correct context assembly without reopening parser bakeoffs.
- Then complete Lambda production acceptance, licensing review, bounded production integration and remaining localization decisions.

## Blockers / gates

- Lambda local research-engine is last verified clean at main@1d461988a9416937a9149e4dd8faeeb666ac0e03 while canonical remote main is f44a20e710f7fb9868eeb2b5a1c654c01f540a48; fast-forward before the A/B gate.
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
