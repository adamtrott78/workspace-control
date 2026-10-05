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
- Local HEAD: 6bc306a254e243dd985c074f005a12ef19c4b78a
- Local clean: true

## Next safe action

Fast-forward the clean Lambda research-engine checkout from main@6bc306a254e243dd985c074f005a12ef19c4b78a to canonical main@5f6eec7b629b4746117f2f0a74d4531c642f8025 with research-engine-daemon.service inactive/dead, then rerun deploy/run-qwen35-bounded-verify-production-gate.sh exactly once. The first gate already proved runtime/weights/quiescence/GPU health but exposed that exact-one-page whole-job eligibility had zero production coverage. The corrected gate must select a real historical full-positive multi-page VERIFY, deterministically partition authoritative evidence by cited page, run one calibrated bounded Qwen unit per page through a single resident model boot, perform zero Codex calls, perform no SemanticResultMaterializer/scientific-state mutation, mutate no production env, leak no model process, and strictly match the stored full-job Codex result on verified boolean, accepted evidence IDs, and issues. Do not run configure-production-local-inference.sh or start sustained production unless this corrected gate PASSes. EXTRACT remains Codex STANDARD.

## Remaining work

- Fast-forward the clean Lambda research-engine main checkout from 6bc306a254e243dd985c074f005a12ef19c4b78a to 5f6eec7b629b4746117f2f0a74d4531c642f8025 with research-engine-daemon.service inactive/dead, then rerun deploy/run-qwen35-bounded-verify-production-gate.sh exactly once. The corrected gate must select a real historical full-positive multi-page VERIFY, derive one calibrated page-scoped Qwen unit per cited page, reuse one Qwen model boot across all page calls, perform zero Codex calls, make no scientific-state or production-env mutation, and strictly equal the stored full-job Codex result.
- Only after the corrected page-scoped VERIFY Lambda gate passes: run deploy/configure-production-local-inference.sh while the daemon is stopped, inspect the timestamped rollback backup, then run deploy/run-lambda-production-acceptance.sh before allowing sustained production. If either gate fails, leave/restore the production env and daemon to the prior Codex-safe state.
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
- Corrected page-scoped bounded Qwen VERIFY routing is merged and CI-validated but is not yet enabled in the live production env. The stopped-daemon Lambda gate must PASS on research-engine main@5f6eec7b629b4746117f2f0a74d4531c642f8025 before running the backup-first production env synchronizer or allowing sustained production.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
