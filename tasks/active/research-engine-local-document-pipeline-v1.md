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
- Remote checkpoint: 42f82d959a93013cee0f3a18122b2e5b3f6773d8
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: a3ba5eb388041c3e00f1cf03a697431f8fd993e3
- Local clean: true

## Next safe action

Keep sustained research disabled and research-engine-daemon.service inactive/dead. research-engine canonical main is 42f82d959a93013cee0f3a18122b2e5b3f6773d8; PR #84 head CI 37256469562 and canonical-main CI 37256559196 both PASS. The first guarded-calibration invocation on Lambda reached clean main@a3ba5eb388041c3e00f1cf03a697431f8fd993e3, verified R0 package reuse and R1 execution certification, performed no package work, then stopped before plan construction/model initialization because the Compose PostgreSQL service was not running after host reboots. That attempt performed zero Qwen calls and is not semantic-quality evidence. First re-inspect branch/HEAD/worktree and fast-forward only if still clean on main from a3ba5eb388041c3e00f1cf03a697431f8fd993e3 to 42f82d959a93013cee0f3a18122b2e5b3f6773d8; do not reset/stash/clean unrelated work. Then run exactly `bash deploy/run-qwen35-guarded-semantic-calibration.sh`. The corrected runner will `docker compose up -d db`, wait boundedly for pg_isready, and keep the research daemon stopped; the db service now has `restart: unless-stopped`, applying durable reboot persistence when Compose reconciles it. After DB readiness, allow only the existing one bounded EXTRACT + one radius-0 VERIFY Qwen calls in one engine session plus their two contemporaneous STANDARD Codex controls. The same natural boot should collect the pending Wave-3 R2/init evidence. Do not rerun the visual benchmark, add C3, install/download Qwen packages, change production routing, or materialize scientific state.

## Remaining work

- Keep sustained research disabled and research-engine-daemon.service inactive/dead. Re-inspect the Lambda checkout and fast-forward only if it is still clean on main from a3ba5eb388041c3e00f1cf03a697431f8fd993e3 to canonical main@42f82d959a93013cee0f3a18122b2e5b3f6773d8; do not reset, stash, clean, or overwrite unrelated work.
- Run exactly `bash deploy/run-qwen35-guarded-semantic-calibration.sh`. The corrected runner will reconcile/start only the PostgreSQL db service, wait for pg_isready, and preserve research-engine-daemon.service inactive/dead. Reconciliation also applies `restart: unless-stopped`, so PostgreSQL should return automatically with Docker after future Lambda reboots.
- This remains the next natural Qwen engine boot and the only Qwen work authorized now: exactly one bounded EXTRACT and one radius-0 VERIFY call in one live engine session, plus two contemporaneous STANDARD Codex controls. The prior DB-stopped attempt performed zero Qwen calls and is not a scientific rerun.
- Do not rerun deploy/run-qwen35-visual-benchmark.sh, do not add C3, do not install/download Qwen packages, and do not test another VLM family.
- Return the visible OUTPUT_ROOT plus calibration-report.json and qwen-runtime-reuse-evidence.json. If the deterministic guard or Qwen-vs-Codex agreement fails, retain Codex and inspect only the relevant qwen-results/codex-control rows; do not broaden the benchmark.
- Use the natural boot's qwen-runtime-reuse-evidence.json to complete Wave-3 R2 and engine-init before/after measurements. Keep R0/R1/R2/R3 separately classified.
- If the calibration decision is PROMOTION_CANDIDATE_GUARDED_BOUNDED_SEMANTICS, open a separate production-integration decision for only the validated residual/job classes with mandatory fail-closed Codex/human fallthrough. Do not silently retier all EXTRACT/VERIFY.
- Retain the separate unresolved PP-OCRv6 scan-source replacement work after the Qwen semantic decision.

## Blockers / gates

- PP-OCRv6 remains resource-pass / quality-not-promoted; the blank scan target still requires replacement with a content-bearing image-only scan before scan-recovery promotion can be evaluated.
- PaddleOCR-VL-1.6 remains not promoted because of resource and semantic-quality failures; no further VLM family bakeoff is open.
- Qwen3.5-4B is the selected local VLM family, but production semantic authority remains Codex STANDARD until the merged guarded EXTRACT/VERIFY calibration gate is executed on Lambda and both local jobs pass deterministic grounding plus contemporaneous Codex agreement.
- The first guarded-calibration invocation after host reboot reached verified R0/R1 reuse but stopped before planning/model initialization because PostgreSQL was not running. PR #84 durably fixes DB boot persistence and runner self-heal; the scientific calibration itself remains unexecuted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
