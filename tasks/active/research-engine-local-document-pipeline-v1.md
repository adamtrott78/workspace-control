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
- Remote checkpoint: a878f74f7d3c669374b12d2a903b56483b3770d7
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: e5aa352d0f0d8d4556539cf5120954d80e8bb4f0
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda cd /home/atrott/adamArchives/Adam/research-engine, require a clean main checkout at e5aa352d0f0d8d4556539cf5120954d80e8bb4f0, fetch origin/main, require origin/main=a878f74f7d3c669374b12d2a903b56483b3770d7, and fast-forward only to that commit. Then rerun bash deploy/configure-production-local-inference.sh, preserve the printed BACKUP/ROLLBACK receipt, and rerun bash deploy/run-lambda-production-acceptance.sh inside the persistent tmux shell with console logging. Return the first ERROR/traceback or the final BUILD ACCEPTANCE REPORT through LAMBDA_PRODUCTION_ACCEPTANCE=PASS.

## Remaining work

- Fast-forward the clean Lambda research-engine checkout from e5aa352d0f0d8d4556539cf5120954d80e8bb4f0 to canonical a878f74f7d3c669374b12d2a903b56483b3770d7 while research-engine-daemon.service remains inactive/dead.
- Rerun deploy/configure-production-local-inference.sh to create a fresh rollback backup and enforce VERIFY radius=0 plus validated shared local-inference settings.
- Rerun deploy/run-lambda-production-acceptance.sh in the persistent tmux shell/log wrapper and evaluate the next fail-closed gate or complete PASS.
- If production acceptance passes, advance to bounded_production_integration; do not start sustained research before that stage is explicitly accepted.

## Blockers / gates

- Lambda local research-engine is last verified clean at main@e5aa352d0f0d8d4556539cf5120954d80e8bb4f0 while canonical remote main is a878f74f7d3c669374b12d2a903b56483b3770d7; fast-forward before rerunning acceptance.
- Lambda production acceptance has not yet passed end-to-end.
- Sustained research remains disabled until production acceptance and bounded production integration are complete.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
