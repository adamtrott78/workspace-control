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
- Remote checkpoint: 8c875a62d44e91ed91207cdc78d715acb0909346
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: a83850016efe2e58b37a86a4203d69af811117a1
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda cd /home/atrott/adamArchives/Adam/research-engine, require a clean main checkout at a83850016efe2e58b37a86a4203d69af811117a1, fetch origin/main, require origin/main=8c875a62d44e91ed91207cdc78d715acb0909346, and fast-forward only to that commit. Keep PostgreSQL db running/healthy and verify the research daemon remains inactive/dead PID 0. Then run bash deploy/run-paper-package-ab-posthoc.sh rf-open-world-corpus-expansion-v1. This gate must make no semantic/model/parser calls and must only compare already-recorded package and current-PDF calibration result summaries. Return the COMPACT CONTEMPORANEOUS POSTHOC SUMMARY, POSTHOC_DECISION, final safety state, or any ERROR/traceback.

## Remaining work

- Fast-forward the clean Lambda research-engine checkout from a83850016efe2e58b37a86a4203d69af811117a1 to canonical 8c875a62d44e91ed91207cdc78d715acb0909346 while research-engine-daemon.service remains inactive/dead.
- Run deploy/run-paper-package-ab-posthoc.sh rf-open-world-corpus-expansion-v1. This is a zero-semantic-call, zero-parser-call comparison over the package/PDF calibration outputs already stored in PostgreSQL.
- If all four controlled pairs pass direct package-vs-current-PDF agreement, combine that result with the 98.59% zero-model quote recovery and two package-history matches to decide the A/B stage quality-safe and advance. If any contemporaneous pair differs materially, inspect that measured context difference before promotion.
- Use contemporaneous controlled-subset token deltas as the cleaner semantic-input efficiency measure; keep historical-relative 8.57% savings as secondary evidence and do not equate tokens with plan allowance.
- After A/B closure, advance to research_pipeline_localization_matrix_validation and finish Lambda production acceptance/licensing.

## Blockers / gates

- Lambda local research-engine is last verified clean at main@a83850016efe2e58b37a86a4203d69af811117a1 while canonical remote main is 8c875a62d44e91ed91207cdc78d715acb0909346; fast-forward before the posthoc comparator.
- Representative history comparison is confounded by model variance: four package arms and their current-PDF controls both fail historical agreement. Direct contemporaneous package-vs-PDF comparison of the already-recorded outputs is required before stage promotion.
- CodeFormulaV2 deployment/redistribution obligations still require final license/deployment review before sustained production enablement.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
