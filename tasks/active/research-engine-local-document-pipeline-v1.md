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
- Remote checkpoint: 5f6eec7b629b4746117f2f0a74d4531c642f8025
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 5f6eec7b629b4746117f2f0a74d4531c642f8025
- Local clean: true

## Next safe action

Perform a bounded daemon boot/health transition only. On Lambda at research-engine main@5f6eec7b629b4746117f2f0a74d4531c642f8025 with the accepted production env and quiescent PostgreSQL state, start research-engine-daemon.service, observe it for a short fixed health window, verify systemd remains active/running with a stable nonzero MainPID and NRestarts=0, verify no nonhuman jobs become QUEUED/RUNNING and no formula/table/Qwen model subprocess appears in the absence of work, then stop the daemon and verify inactive/dead PID 0. Do not submit scientific work, do not rerun Qwen/Codex, and do not resume sustained research until this boot/health result is checkpointed. EXTRACT remains Codex STANDARD; page-scoped bounded VERIFY is enabled in the accepted production env.

## Remaining work

- Perform one bounded daemon boot/health transition on Lambda with main@5f6eec7b629b4746117f2f0a74d4531c642f8025 and the accepted production env: start research-engine-daemon.service, observe a short stable health window, verify is-active=active, SubState=running, MainPID nonzero, NRestarts remains 0, no queued/running nonhuman jobs appear, and no formula/table/Qwen model subprocess spawns without work; then stop the daemon and verify inactive/dead PID 0.
- Only after the bounded daemon boot/health transition PASS is durably checkpointed: decide whether to resume sustained daemon operation for the owning research task. Do not start new scientific work merely to exercise Qwen VERIFY.
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
- Production env and stopped-daemon Lambda acceptance are PASS, but sustained research is still gated on a separate bounded daemon boot/health transition. Start the daemon only for a short health window, verify stable systemd state with no restart loop and no unexpected nonhuman work/model spawn, then stop and checkpoint before enabling sustained operation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
