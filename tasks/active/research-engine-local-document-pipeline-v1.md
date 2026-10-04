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

Keep research-engine-daemon.service inactive/dead and do not START sustained research. Wait for research-engine PR #63 (Docling sidecar runtime-output discovery hotfix) to merge and canonical-main CI to pass. Then fast-forward the clean Lambda checkout from a71a1bb04b0cdec0116e906dfed0d7aefd9f5b86 to that exact canonical main and rerun bash deploy/run-bounded-production-integration.sh inside the persistent tmux/log wrapper. The hotfix must discover the actual SHA-stemmed Docling native/standard/ACCURATE JSON artifact rather than assuming source.json. Return the first structured sidecar FAIL receipt/traceback or the final bounded integration report. If bounded integration passes, advance next to residual_escalation_and_local_semantic_fallbacks, not completion.

## Remaining work

- Merge research-engine PR #63 after CI and require canonical-main CI PASS.
- Fast-forward the clean Lambda checkout to the merged hotfix, refresh the managed production env only if required, and rerun deploy/run-bounded-production-integration.sh.
- Require sidecar miss->hit, telemetry, bounded idle-daemon worker registration, cleanup and unchanged scientific fingerprints.
- After bounded integration PASS, advance to residual_escalation_and_local_semantic_fallbacks rather than directly to completion.
- In that stage, classify remaining parser/semantic residuals and benchmark only justified OCR/VLM/local-agent candidates before defining deterministic -> specialized -> local multimodal/agent -> Codex -> human escalation.

## Blockers / gates

- Bounded production integration is blocked only on the Docling runtime-output naming defect fixed by research-engine PR #63; merge/canonical CI and Lambda retry are required.
- The complete residual escalation/local semantic fallback ladder (including VLM/local-agent candidates) is intentionally not yet built; a new stage now follows bounded production integration before completion.
- Sustained research remains disabled until bounded production integration passes and residual escalation/local semantic fallback decisions are validated.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
