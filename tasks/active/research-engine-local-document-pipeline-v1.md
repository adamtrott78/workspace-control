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
- Remote checkpoint: 7e7a5575bbde84224290ce72a2c4c095b70d7aca
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: e9ed7d17e91a8a221aa9f8c4b80793b6f5ce0198
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda, first verify /home/atrott/adamArchives/Adam/research-engine is clean on main@e9ed7d17e91a8a221aa9f8c4b80793b6f5ce0198, fetch origin/main, require origin/main=7e7a5575bbde84224290ce72a2c4c095b70d7aca, and fast-forward only to that exact commit. Then begin local_inference_service_and_concurrency: design and CI-gate one shared local model-serving/ownership contract for the validated CodeFormulaV2 equation path and Paddle PP-TableMagic persistent-empty-grid table fallback so concurrent PDFs cannot load duplicate heavyweight model instances. Preserve native+standard routing, region/page bounds, original-PDF authority, visible workspace-control-tmp operator artifacts, and fail-closed escalation semantics. Do not restart sustained research or reopen broad parser families.

## Remaining work

- Fast-forward the clean Lambda research-engine checkout from e9ed7d17e91a8a221aa9f8c4b80793b6f5ce0198 to canonical 7e7a5575bbde84224290ce72a2c4c095b70d7aca while the daemon remains inactive/dead.
- Design and CI-gate a shared local inference service/concurrency contract that keeps CodeFormulaV2 and Paddle PP-TableMagic resident or otherwise serializes model ownership so multiple concurrent PDFs cannot duplicate heavyweight model loads.
- Integrate the validated equation-only and persistent-empty-grid table escalation routes with that service while retaining region/page bounds, provenance, original-PDF authority, and fail-closed behavior.
- Run stopped-daemon Lambda concurrency/resource tests for multiple simultaneous document jobs and record GPU/VRAM/RAM/model-load behavior.
- Then advance to EXTRACT/VERIFY paper-package A/B validation and the broader research-pipeline localization matrix.

## Blockers / gates

- Lambda local research-engine is last verified clean at main@e9ed7d17e91a8a221aa9f8c4b80793b6f5ce0198 while canonical remote main is 7e7a5575bbde84224290ce72a2c4c095b70d7aca; fast-forward before shared-serving work.
- CodeFormulaV2 and Paddle PP-TableMagic have validated quality paths but still run from isolated benchmark runtimes. They need a shared local inference/concurrency design before production use so concurrent PDFs do not duplicate heavyweight model loads.
- CodeFormulaV2 deployment/redistribution obligations still require final license/deployment review before production promotion.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
