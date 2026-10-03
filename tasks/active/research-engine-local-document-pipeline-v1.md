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
- Remote checkpoint: e5aa352d0f0d8d4556539cf5120954d80e8bb4f0
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 8c875a62d44e91ed91207cdc78d715acb0909346
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda cd /home/atrott/adamArchives/Adam/research-engine, require a clean main checkout at 8c875a62d44e91ed91207cdc78d715acb0909346, fetch origin/main, require origin/main=e5aa352d0f0d8d4556539cf5120954d80e8bb4f0, and fast-forward only to that commit. Re-verify daemon inactive/dead PID 0. Then run bash deploy/configure-production-local-inference.sh and retain its BACKUP/ROLLBACK output. Without starting the daemon, run bash deploy/run-lambda-production-acceptance.sh. Return any ERROR line or, on success, the BUILD ACCEPTANCE REPORT / FINAL SAFETY STATE including LAMBDA_PRODUCTION_ACCEPTANCE=PASS. The acceptance gate may start/check PostgreSQL only and must perform no semantic/model inference or scientific-state materialization.

## Remaining work

- Fast-forward the clean Lambda research-engine checkout from 8c875a62d44e91ed91207cdc78d715acb0909346 to canonical e5aa352d0f0d8d4556539cf5120954d80e8bb4f0 while research-engine-daemon.service remains inactive/dead.
- Run deploy/configure-production-local-inference.sh once. Preserve the printed timestamped env backup/rollback path and keep the daemon stopped.
- Run deploy/run-lambda-production-acceptance.sh. It may start/check PostgreSQL only; it must fail closed on non-quiescent research work and leave the research daemon inactive/dead.
- Evaluate the acceptance report: systemd/env drift, queue quiescence, runtime/cache availability, two GPU probes, zero-spawn broker construction, authoritative-PDF hydration and read-only ops health.
- If PASS, validate lambda_production_acceptance and advance to bounded_production_integration; do not start sustained research yet.

## Blockers / gates

- Lambda local research-engine is last verified clean at main@8c875a62d44e91ed91207cdc78d715acb0909346 while canonical remote main is e5aa352d0f0d8d4556539cf5120954d80e8bb4f0; fast-forward before production acceptance.
- The live ~/.research-engine/research-engine.env has not yet been synchronized with the validated shared local-inference block; use the backup-first configurator while the daemon is stopped.
- The bounded Lambda production-acceptance gate has not yet been executed on canonical main.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
