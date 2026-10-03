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
- Local HEAD: a878f74f7d3c669374b12d2a903b56483b3770d7
- Local clean: true

## Next safe action

Keep sustained research disabled. Treat research-engine main@a878f74f7d3c669374b12d2a903b56483b3770d7 as the validated Lambda production-acceptance baseline. Begin bounded_production_integration by inspecting the current document-sidecar/compiler/router integration, feature/config gates, telemetry, daemon startup/worker registration, and rollback behavior. Preserve authoritative-PDF EXTRACT/VERIFY hydration and do not promote paper-package semantic context. Design and CI-gate a finite integration runner that fails closed unless PostgreSQL is quiescent, starts research-engine-daemon.service only for a bounded health interval with no runnable non-human jobs, verifies expected workers/broker configuration, stops the daemon unconditionally, and leaves no scientific-state mutation.

## Remaining work

- Design and CI-gate bounded production integration behind explicit configuration/feature controls while preserving authoritative-PDF EXTRACT/VERIFY semantics.
- Integrate/verify content-addressed document-sidecar caching and telemetry for document compiler/router/local-model usage without making paper-package context the semantic baseline.
- Add a rollback-capable bounded daemon lifecycle gate that first requires no RUNNING research runs or QUEUED/RUNNING non-human work, starts the daemon only for a finite health/worker registration interval, verifies shared broker ownership/configuration without launching research jobs, then stops the daemon and confirms cleanup.
- Where model-server lifecycle must be exercised, use only bounded preselected document-sidecar smoke work with no scientific-state materialization and explicit rollback; otherwise reuse the already-passed local-inference concurrency evidence.
- After bounded integration PASS, decide whether the task can be closed or whether a final deliberately bounded production comparison is still required before any sustained research enablement.

## Blockers / gates

- Bounded production integration has not yet demonstrated an explicit rollback-capable daemon lifecycle with the validated local document pipeline enabled.
- Paper-package-derived context remains prohibited as the production EXTRACT/VERIFY semantic baseline; bounded integration must preserve authoritative-PDF hydration and use local document compilation only as validated support/escalation/cache behavior.
- Sustained research remains disabled until bounded production integration passes.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
