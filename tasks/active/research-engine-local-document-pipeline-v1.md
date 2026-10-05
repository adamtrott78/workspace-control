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
- Remote checkpoint: a3ba5eb388041c3e00f1cf03a697431f8fd993e3
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: a3d80e9329e231889b11430f98c0de342349fe1f
- Local clean: true

## Next safe action

Keep sustained research disabled and research-engine-daemon.service inactive/dead. research-engine canonical main is a3ba5eb388041c3e00f1cf03a697431f8fd993e3; PR #83 head CI 37255866525 and canonical-main CI 37255961585 both PASS. Qwen3.5-4B is already selected as the local VLM family; do not rerun the exact three-call visual benchmark and do not test another VLM. Lambda/local is last verified clean on main@a3d80e9329e231889b11430f98c0de342349fe1f. First re-inspect branch/HEAD/worktree and fast-forward only if still clean on main to a3ba5eb388041c3e00f1cf03a697431f8fd993e3; do not reset/stash/clean unrelated work. Keep the daemon stopped. Then run exactly `bash deploy/run-qwen35-guarded-semantic-calibration.sh`. The merged gate requires the existing native-sampler-v3 certified package environment and performs no install/download; it selects exactly one bounded EXTRACT and one radius-0 VERIFY preserved ambiguity case, serves both from one Qwen engine boot, deterministically rejects ungrounded/unbounded output, runs contemporaneous STANDARD Codex controls on the same authoritative-PDF contexts, invokes no SemanticResultMaterializer, changes no production routing, and materializes no scientific state. This same natural boot records the pending Wave-3 R2/engine-init evidence without any C3 or extra certification inference. Return OUTPUT_ROOT, calibration-report.json, and qwen-runtime-reuse-evidence.json; only include qwen-results.json/codex-control-results.json if adjudication needs row-level diagnosis.

## Remaining work

- Keep sustained research disabled and research-engine-daemon.service inactive/dead. Re-inspect the Lambda checkout and fast-forward only if it is still clean on main from a3d80e9329e231889b11430f98c0de342349fe1f to canonical main@a3ba5eb388041c3e00f1cf03a697431f8fd993e3; do not reset, stash, clean, or overwrite unrelated work.
- Run exactly `bash deploy/run-qwen35-guarded-semantic-calibration.sh`. This is the next natural Qwen engine boot and the only Qwen work authorized now: exactly two semantic calls in one engine session, plus two contemporaneous STANDARD Codex controls.
- Do not rerun deploy/run-qwen35-visual-benchmark.sh, do not add C3, do not install/download Qwen packages, and do not test another VLM family.
- Return the visible OUTPUT_ROOT plus calibration-report.json and qwen-runtime-reuse-evidence.json. If the deterministic guard or Qwen-vs-Codex agreement fails, retain Codex and inspect only the relevant qwen-results/codex-control rows; do not broaden the benchmark.
- Use the natural boot's qwen-runtime-reuse-evidence.json to complete Wave-3 R2 and engine-init before/after measurements. Keep R0/R1/R2/R3 separately classified.
- If the calibration decision is PROMOTION_CANDIDATE_GUARDED_BOUNDED_SEMANTICS, open a separate production-integration decision for only the validated residual/job classes with mandatory fail-closed Codex/human fallthrough. Do not silently retier all EXTRACT/VERIFY.
- Retain the separate unresolved PP-OCRv6 scan-source replacement work after the Qwen semantic decision.

## Blockers / gates

- PP-OCRv6 remains resource-pass / quality-not-promoted; the blank scan target still requires replacement with a content-bearing image-only scan before scan-recovery promotion can be evaluated.
- PaddleOCR-VL-1.6 remains not promoted because of resource and semantic-quality failures; no further VLM family bakeoff is open.
- Qwen3.5-4B is the selected local VLM family, but production semantic authority remains Codex STANDARD until the merged guarded EXTRACT/VERIFY calibration gate is executed on Lambda and both local jobs pass deterministic grounding plus contemporaneous Codex agreement.
- The guarded calibration has not yet been executed on Lambda. Lambda/local remains last verified clean on main@a3d80e9329e231889b11430f98c0de342349fe1f; canonical research-engine main is now a3ba5eb388041c3e00f1cf03a697431f8fd993e3.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
