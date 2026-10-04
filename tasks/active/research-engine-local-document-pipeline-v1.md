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
- Remote checkpoint: 0e5b1464c5307b9b1824618b6e5cff0f13485146
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: a71a1bb04b0cdec0116e906dfed0d7aefd9f5b86
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On Lambda cd /home/atrott/adamArchives/Adam/research-engine, require a clean main checkout at a71a1bb04b0cdec0116e906dfed0d7aefd9f5b86, fetch origin/main, require origin/main=0e5b1464c5307b9b1824618b6e5cff0f13485146, and fast-forward only to that commit. Then rerun bash deploy/run-bounded-production-integration.sh inside the persistent tmux/log wrapper. The hotfix must discover SHA-stemmed native/standard/ACCURATE Docling JSON artifacts automatically. Return the first structured sidecar FAIL receipt/traceback or the final bounded integration report through BOUNDED_PRODUCTION_INTEGRATION=PASS. If PASS, advance next to residual_escalation_and_local_semantic_fallbacks, not completion.

## Remaining work

- Fast-forward Lambda from a71a1bb04b0cdec0116e906dfed0d7aefd9f5b86 to canonical 0e5b1464c5307b9b1824618b6e5cff0f13485146 while the daemon remains inactive/dead.
- Rerun deploy/run-bounded-production-integration.sh. The managed env does not require another semantic-policy change; refresh via deploy/configure-production-local-inference.sh only if the live env receipt/settings are uncertain.
- Require sidecar COMPLETED then CACHE_HIT, telemetry, bounded idle-daemon worker registration, no model-server leak, final inactive/dead daemon, and unchanged scientific fingerprints.
- On PASS, advance to residual_escalation_and_local_semantic_fallbacks and benchmark measured residuals for OCR/VLM/local-agent escalation before any task completion or sustained research enablement.

## Blockers / gates

- Lambda local research-engine is last verified clean at main@a71a1bb04b0cdec0116e906dfed0d7aefd9f5b86 while canonical remote main is 0e5b1464c5307b9b1824618b6e5cff0f13485146; fast-forward before bounded integration retry.
- Bounded production integration has not yet passed on Lambda after the output-discovery hotfix.
- Residual escalation/local semantic fallback architecture remains a planned post-bounded stage; Codex STANDARD EXTRACT/VERIFY remains the semantic baseline until that stage validates cheaper local fallbacks.
- Sustained research remains disabled.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
