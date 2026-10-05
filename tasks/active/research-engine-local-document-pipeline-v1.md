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
- Remote checkpoint: 2a12b907bf509a21c088b6ee865d5672b567a676
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 2a12b907bf509a21c088b6ee865d5672b567a676
- Local clean: true

## Next safe action

CHECKPOINT_AND_STOP for the grounded-candidate EXTRACT scope. Retain Codex STANDARD as the production EXTRACT baseline: the corrected guard replay passed provenance grounding but failed the declared semantic-equivalence thresholds (coverage=0.0, precision=0.0, matched normalized F1=0.211106570774763, page/type agreement on passing matches=0.0), so Qwen grounded EXTRACT is not promoted. Do not rerun Qwen, Codex, C3/C4, or reopen model shopping from this evidence. The next separate decision, only if explicitly authorized, is production integration for the already-validated bounded VERIFY residual class. Preserve R2=PRESENT_UNVERIFIED and corrected R3=NOT_APPLICABLE; do not manufacture telemetry.

## Remaining work

- Do not rerun the completed guarded semantic calibration and do not rerun the visual benchmark. Preserve research-engine-daemon.service inactive/dead and keep Codex STANDARD as the production semantic baseline.
- Open a separate production-integration decision for the validated bounded VERIFY residual class only after the EXTRACT diagnosis is recorded; do not silently retier all VERIFY jobs.
- Record natural Wave-3 adoption evidence as R0=REUSED, R1=VERIFIED_HIT, R2=PRESENT_UNVERIFIED, R3=REUSED with the observed timing improvements. Do not manufacture another boot or C3 call solely to turn R2/C3 green.
- When future owning scientific work naturally authorizes a same-modality canary and C4 in one live engine session, adopt the shared workspace-control C0-C4/operation receipt framework and reassess WAVE_3_FREEZE_READY.
- Retain the separate unresolved PP-OCRv6 scan-source replacement work after the Qwen semantic integration decision.
- If the user later authorizes production integration, scope that decision to the already-validated bounded VERIFY residual class only; do not retier all VERIFY jobs and do not reopen grounded EXTRACT or model-family bakeoff from this failed EXTRACT control.

## Blockers / gates

- PP-OCRv6 remains resource-pass / quality-not-promoted; the blank scan target still requires replacement with a content-bearing image-only scan before scan-recovery promotion can be evaluated.
- PaddleOCR-VL-1.6 remains not promoted because of resource and semantic-quality failures; no further VLM family bakeoff is open.
- Qwen3.5-4B bounded VERIFY now has one successful guarded Qwen-vs-Codex calibration case and is a validated promotion candidate for that narrow residual class, but no production-routing change is authorized yet.
- R2 compiled/JIT reuse remains PRESENT_UNVERIFIED despite large natural-boot timing reductions because the runtime log exposed no explicit reuse marker. Do not rerun solely to strengthen telemetry.
- Shared Wave-3 runtime_certified=true / WAVE_3_FREEZE_READY remain false until a naturally authorized C3 same-modality canary can share a live engine with C4; do not run C3 solely for telemetry.
- Qwen3.5-4B grounded-candidate EXTRACT is not promoted. The corrected guard passes, but the offline Qwen-vs-STANDARD-Codex control failed all predeclared semantic-equivalence thresholds; retain Codex STANDARD as the EXTRACT production baseline.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
