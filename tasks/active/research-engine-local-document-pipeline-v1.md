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

Perform one corrected bounded daemon boot/health transition only. On Lambda at research-engine main@5f6eec7b629b4746117f2f0a74d4531c642f8025 with the accepted production env, first verify research-engine-daemon.service is inactive/dead PID 0, PostgreSQL is ready/quiescent, and no formula/table/Qwen model subprocess exists. Capture the stopped-unit NRestarts value as PRE_NRESTARTS; do not reset or require it to be zero. Start the daemon, observe the same short fixed health window, and require active/running with a stable nonzero MainPID while NRestarts remains exactly PRE_NRESTARTS at each observation (restart_delta=0). Require no nonhuman job becomes QUEUED/RUNNING and no model subprocess spawns in the absence of work. Then stop the daemon and verify inactive/dead PID 0 and zero model-process leak. If the current window fails, collect journal entries bounded to the gate start timestamp; do not use an unbounded journal tail. Do not submit scientific work and do not rerun Qwen/Codex. The previous boot-health attempt is classified as a false-negative test assertion caused by five historical October 3 automatic restarts during PostgreSQL unavailability, not as an October 5 daemon crash. After a corrected health PASS, checkpoint before deciding whether to leave the daemon running for sustained research.

## Remaining work

- Perform one corrected bounded daemon boot/health transition on Lambda at research-engine main@5f6eec7b629b4746117f2f0a74d4531c642f8025 with the accepted production env. First verify daemon inactive/dead PID 0 and DB quiescence; capture PRE_NRESTARTS before start; start the daemon; require active/running with a stable nonzero MainPID at the initial and fixed health windows and require NRestarts to remain exactly PRE_NRESTARTS (restart_delta=0), not absolute zero; require no queued/running nonhuman work and no formula/table/Qwen subprocess without work; stop the daemon and verify inactive/dead PID 0 plus zero model-process leak. On failure, collect journal entries only since the gate start timestamp.
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
- Production env and stopped-daemon Lambda acceptance are PASS. The first bounded daemon boot-health gate false-failed because it required absolute NRestarts=0 even though the unit retained five historical automatic restarts from the October 3 PostgreSQL outage. Sustained operation remains gated only on one corrected short health window using restart-counter delta=0, stable MainPID, quiescent DB, zero lazy model spawn, clean stop, and current-window journal diagnostics if needed.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
