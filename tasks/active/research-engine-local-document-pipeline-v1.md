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
- Remote checkpoint: a72bc737ab22167af0b3ab7b95d01579810711e5
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 42f82d959a93013cee0f3a18122b2e5b3f6773d8
- Local clean: true

## Next safe action

Keep sustained research disabled and research-engine-daemon.service inactive/dead. research-engine canonical main is a72bc737ab22167af0b3ab7b95d01579810711e5; PR #85 final-head CI 37257370787 and canonical-main CI 37258159731 both PASS. Lambda/local is last verified clean on main@42f82d959a93013cee0f3a18122b2e5b3f6773d8. The latest calibration attempt verified R0 environment reuse and R1 certification reuse and restored PostgreSQL, then failed during plan construction before GPU selection/model init/QWEN_CALL_START because the old planner hydrated whole PDFs and could not derive a bounded VERIFY control; zero Qwen and zero Codex calls occurred. First re-inspect branch/HEAD/worktree and fast-forward only if still clean on main from 42f82d959a93013cee0f3a18122b2e5b3f6773d8 to a72bc737ab22167af0b3ab7b95d01579810711e5; do not reset/stash/clean unrelated work. Then run exactly `bash deploy/run-qwen35-guarded-semantic-calibration.sh`. PR #85 now extracts only authorized pages, derives a deterministic single-page VERIFY evidence cluster from preserved controls, quote-windows oversized cited pages only when every authoritative quote can be preserved, and supplies the identical bounded context to Qwen and STANDARD Codex. Keep the exact two-call semantic calibration contract, PostgreSQL self-heal, native-sampler-v3 runtime identity, no install/download, no visual rerun, no extra C3 telemetry call, no production routing change, and no scientific-state materialization. Collect R2/init reuse evidence opportunistically from this natural boot under the shared Wave-3 model; keep R0/R1/R2/R3 distinct.

## Remaining work

- Keep sustained research disabled and research-engine-daemon.service inactive/dead. Re-inspect the Lambda checkout and fast-forward only if it is still clean on main from 42f82d959a93013cee0f3a18122b2e5b3f6773d8 to canonical main@a72bc737ab22167af0b3ab7b95d01579810711e5; do not reset, stash, clean, or overwrite unrelated work.
- Run exactly `bash deploy/run-qwen35-guarded-semantic-calibration.sh`. The corrected planner extracts only authorized PDF pages, derives one deterministic page-scoped VERIFY evidence cluster, and quote-windows only when necessary. PostgreSQL self-heal remains active and the research daemon must remain stopped.
- This is still the next natural Qwen engine boot and the only Qwen work authorized now: exactly one bounded EXTRACT and one radius-0 VERIFY call in one live engine session, plus two contemporaneous STANDARD Codex controls. Both previous calibration attempts performed zero Qwen calls.
- Do not rerun deploy/run-qwen35-visual-benchmark.sh, do not add C3 solely for telemetry, do not install/download Qwen packages, and do not test another VLM family.
- Use the shared Wave-3 execution model from workspace-control main@c46700c3a54a1783d74e9404d9685e7fab09f7f6 conceptually for this natural workload: keep R0/R1/R2/R3 distinct; do not call cache presence an R2 hit; do not claim reusable runtime_certified unless C0-C3 are all PASS for the same identity. Do not delay the scientific run merely to refactor project-local code onto the shared helper.
- Return OUTPUT_ROOT plus calibration-report.json and qwen-runtime-reuse-evidence.json. If plan construction still fails, return the compact explicit rejection diagnostics; if the guard/Codex comparison fails, retain Codex and inspect only the relevant rows.
- Use the same natural engine boot's reuse evidence to complete Wave-3 R2 compile/JIT and engine-init before/after measurements. Keep C3 separate; only execute it later when naturally authorized and able to share the same live engine with C4.
- If calibration returns PROMOTION_CANDIDATE_GUARDED_BOUNDED_SEMANTICS, open a separate production-integration decision for only validated residual/job classes with mandatory fail-closed Codex/human fallthrough.
- Retain the separate unresolved PP-OCRv6 scan-source replacement work after the Qwen semantic decision.

## Blockers / gates

- PP-OCRv6 remains resource-pass / quality-not-promoted; the blank scan target still requires replacement with a content-bearing image-only scan before scan-recovery promotion can be evaluated.
- PaddleOCR-VL-1.6 remains not promoted because of resource and semantic-quality failures; no further VLM family bakeoff is open.
- Qwen3.5-4B is the selected local VLM family, but production semantic authority remains Codex STANDARD until the merged guarded EXTRACT/VERIFY calibration gate executes successfully and both local jobs pass deterministic grounding plus contemporaneous Codex agreement.
- The latest guarded-calibration attempt stopped during plan construction before any Qwen/Codex call because the old planner hydrated whole PDFs and could not derive a bounded VERIFY control. PR #85 fixes that planner boundary and is fully CI-validated; the corrected calibration has not yet been run on Lambda.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
