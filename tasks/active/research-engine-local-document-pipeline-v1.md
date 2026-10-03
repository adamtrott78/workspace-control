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

Keep research-engine-daemon.service inactive/dead and do not START sustained research. Wait for research-engine PR #61 (production-env VERIFY-radius hotfix) to merge and canonical-main CI to pass. Then fast-forward the clean Lambda checkout from e5aa352d0f0d8d4556539cf5120954d80e8bb4f0 to that exact canonical main, rerun bash deploy/configure-production-local-inference.sh to create a fresh rollback backup and enforce RESEARCH_ENGINE_VERIFY_PAGE_RADIUS=0 plus the validated broker settings, then rerun bash deploy/run-lambda-production-acceptance.sh. Return the first ERROR/traceback or the final acceptance report.

## Remaining work

- Merge PR #61 after CI and require canonical-main CI PASS.
- Fast-forward Lambda to the resulting canonical main while research-engine-daemon.service remains inactive/dead.
- Rerun deploy/configure-production-local-inference.sh to create a fresh backup and set VERIFY radius=0 plus validated local-inference settings.
- Rerun deploy/run-lambda-production-acceptance.sh and evaluate the first subsequent fail-closed gate or complete PASS.
- If production acceptance passes, advance to bounded_production_integration; do not start sustained research before that stage is explicitly accepted.

## Blockers / gates

- Live Lambda production env has stale RESEARCH_ENGINE_VERIFY_PAGE_RADIUS != 0; PR #61 hotfix must merge, Lambda must fast-forward, and the rollback-safe env synchronizer must be rerun before acceptance.
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
