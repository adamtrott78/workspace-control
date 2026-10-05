<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-document-pipeline-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-document-pipeline-v1
- Title: Research Engine Local Document Intelligence and Compute Offload v1
- Status: CHECKPOINTED
- Capsule schema: v2

## Goal

Design, benchmark, and integrate a provenance-preserving local document-intelligence pipeline that converts content-addressed research PDFs into reusable LLM-ready paper packages, minimizes paid/plan semantic usage and repeated PDF interpretation, and systematically evaluates every research-engine stage for safe deterministic or local-model offload before production deployment on the Lambda.

## Parent execution owner

automated-research-engine-v1

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 134d60630a1bf16499fee169f28456a670de343f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 5f6eec7b629b4746117f2f0a74d4531c642f8025
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 5f6eec7b629b4746117f2f0a74d4531c642f8025
- Local clean: true

## Current stage

residual_escalation_and_local_semantic_fallbacks

## Next safe action

CHECKPOINTED. The production local-document pipeline and bounded page-scoped Qwen VERIFY integration remain accepted at research-engine@5f6eec7b629b4746117f2f0a74d4531c642f8025 and must not be reopened merely for more validation. The explicitly reopened mostly-local EXTRACT research is now owned by child task `research-engine-local-extract-redesign-v1`. Resume this parent only if the accepted production document/VERIFY implementation itself requires new work or another deferred parent-owned residual is explicitly authorized.

## Remaining work

- Production local-document/Qwen-VERIFY integration is accepted through the corrected bounded daemon boot-health gate. The daemon is intentionally left inactive/dead after the bounded test. Resume sustained daemon operation only when the owning automated-research-engine task explicitly resumes scientific work; do not start work merely to exercise local VERIFY.
- Do not rerun the completed guarded semantic calibration and do not rerun the visual benchmark. Preserve research-engine-daemon.service inactive/dead and keep Codex STANDARD as the production semantic baseline.
- Record natural Wave-3 adoption evidence as R0=REUSED, R1=VERIFIED_HIT, R2=PRESENT_UNVERIFIED, R3=REUSED with the observed timing improvements. Do not manufacture another boot or C3 call solely to turn R2/C3 green.
- When future owning scientific work naturally authorizes a same-modality canary and C4 in one live engine session, adopt the shared workspace-control C0-C4/operation receipt framework and reassess WAVE_3_FREEZE_READY.
- Retain the separate unresolved PP-OCRv6 scan-source replacement work after the Qwen semantic integration decision.

## Blockers / gates

- PP-OCRv6 remains resource-pass / quality-not-promoted; the blank scan target still requires replacement with a content-bearing image-only scan before scan-recovery promotion can be evaluated.
- PaddleOCR-VL-1.6 remains not promoted because of resource and semantic-quality failures; no further VLM family bakeoff is open.
- R2 compiled/JIT reuse remains PRESENT_UNVERIFIED despite large natural-boot timing reductions because the runtime log exposed no explicit reuse marker. Do not rerun solely to strengthen telemetry.
- Qwen3.5-4B grounded-candidate EXTRACT is not promoted. The corrected guard passes, but the offline Qwen-vs-STANDARD-Codex control failed all predeclared semantic-equivalence thresholds; retain Codex STANDARD as the EXTRACT production baseline.
- DEFERRED_FOLLOWUP: semantic workers currently honor the global Codex provider-backoff before leasing work, so a Qwen-eligible VERIFY may wait during an active Codex plan backoff. Do not broaden the bounded VERIFY production gate to redesign worker backoff unless future evidence shows this materially blocks local VERIFY availability.
- DEFERRED_FOLLOWUP: the gate receipt reports Qwen input_tokens=2 per page request (aggregate 6), which is implausibly low and suggests local prompt-token telemetry undercounting. This does not affect vLLM generation, deterministic guards, or Codex agreement; do not delay production acceptance solely for this telemetry issue, but do not use these token counts for efficiency claims until corrected.
- Production gate is no longer blocked: production env acceptance and corrected bounded daemon boot-health both PASS at research-engine@5f6eec7b629b4746117f2f0a74d4531c642f8025. The daemon remains intentionally stopped after the bounded acceptance window; sustained operation is a later owning-task decision, not additional validation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
