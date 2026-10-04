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
- Remote checkpoint: a71a1bb04b0cdec0116e906dfed0d7aefd9f5b86
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: a878f74f7d3c669374b12d2a903b56483b3770d7
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead before the gate and do not START sustained research. On Lambda cd /home/atrott/adamArchives/Adam/research-engine, require a clean main checkout at a878f74f7d3c669374b12d2a903b56483b3770d7, fetch origin/main, require origin/main=a71a1bb04b0cdec0116e906dfed0d7aefd9f5b86, and fast-forward only to that commit. Rerun bash deploy/configure-production-local-inference.sh and preserve its fresh BACKUP/ROLLBACK receipt. Then, inside the persistent tmux shell with console logging, run bash deploy/run-bounded-production-integration.sh. The runner may start research-engine-daemon.service only for its finite idle lifecycle after proving there are no RUNNING research runs or QUEUED/RUNNING non-HUMAN jobs; it must stop the daemon unconditionally. Return the first ERROR/traceback or the final bounded integration report through BOUNDED_PRODUCTION_INTEGRATION=PASS.

## Remaining work

- Fast-forward the clean Lambda checkout from a878f74f7d3c669374b12d2a903b56483b3770d7 to canonical a71a1bb04b0cdec0116e906dfed0d7aefd9f5b86 while the research daemon remains inactive/dead.
- Rerun deploy/configure-production-local-inference.sh to create a fresh rollback backup and enable the managed document-sidecar gates/timeouts in the live env.
- Run deploy/run-bounded-production-integration.sh in the persistent tmux/log wrapper. The gate will apply the idempotent sidecar telemetry schema, require queue quiescence, build/cache one derived sidecar, then perform one finite idle daemon lifecycle and stop.
- Evaluate sidecar routing/model usage, cache miss->hit, telemetry, worker registration, process cleanup and scientific fingerprint invariance.
- If PASS, close bounded_production_integration and decide whether this task is complete and sustained research can be separately enabled under the established operator controls.

## Blockers / gates

- Lambda local research-engine is last verified clean at main@a878f74f7d3c669374b12d2a903b56483b3770d7 while canonical remote main is a71a1bb04b0cdec0116e906dfed0d7aefd9f5b86; fast-forward before bounded integration.
- Bounded production integration has not yet been measured on the Lambda host.
- Sustained research remains disabled until bounded production integration passes and the final task closure decision is recorded.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
