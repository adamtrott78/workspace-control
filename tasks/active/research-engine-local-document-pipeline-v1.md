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
- Remote checkpoint: 243ce2601b7f39231f0bbdaaf402874070be2ab4
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: a3d80e9329e231889b11430f98c0de342349fe1f
- Local clean: true

## Next safe action

Keep sustained research disabled and research-engine-daemon.service inactive/dead. research-engine canonical main is 243ce2601b7f39231f0bbdaaf402874070be2ab4; PR #82 head CI 37254700478 and canonical-main CI 37254821768 both PASS. The exact Qwen3.5-4B three-call visual benchmark on clean Lambda main@a3d80e9329e231889b11430f98c0de342349fe1f completed successfully and must not be rerun: 3/3 calls, valid structured outputs, model init 117.64840551599627 s, peak GPU delta 11989 MiB, peak RSS 5807.02734375 MiB, warm max 5.179953836006462 s, 2/2 crop reuse, no package install/download, no scientific-state materialization or production-routing change. The contemporaneous STANDARD Codex control agrees on Figure 6 and establishes the exact Figure 3 same-width identity-shortcut relation; Qwen is now the selected local VLM family, but free-text relation output remains guarded and Codex STANDARD stays the production baseline. Do not test another VLM and do not rerun Qwen for Wave-3. Next, implement on GitHub a narrow guarded Qwen residual adapter and bounded local EXTRACT/VERIFY calibration harness that preserves authoritative PDF/page/bbox/caption/model provenance, safely canonicalizes only deterministic structured fields, rejects/abstains on unsupported relations, and falls through to REMOTE_CODEX_AUTHORITATIVE_PDF. After that code passes PR and canonical-main CI, perform one bounded natural Lambda calibration run; collect R0/R1/R2/R3 and engine/compile/warmup reuse evidence opportunistically from that same boot without extra certification calls.

## Remaining work

- Keep sustained research disabled and research-engine-daemon.service inactive/dead. Do not rerun the completed exact three-call Qwen visual benchmark and do not open another VLM family bakeoff.
- Implement a narrow guarded Qwen visual/semantic residual adapter plus bounded downstream EXTRACT/VERIFY calibration harness on canonical research-engine main@243ce2601b7f39231f0bbdaaf402874070be2ab4. Preserve source PDF SHA, page/bbox, linked caption context, model/runtime lineage, structured field confidence/validation, and explicit authoritative-PDF Codex fallthrough.
- Canonicalize only intrinsically safe structured fields (for example stable de-duplication of repeated stage-width labels). Do not rewrite or infer unsupported semantic relations; an unvalidated/disagreeing relation must abstain/fall through.
- After the guarded calibration implementation is CI-validated and merged, re-inspect the Lambda checkout and fast-forward only if it is still clean on main from its last verified local head a3d80e9329e231889b11430f98c0de342349fe1f to the new canonical checkpoint; do not reset/stash/clean unrelated work.
- Run the bounded downstream calibration once. That natural Qwen engine boot may opportunistically record R0/R1/R2/R3 reuse, total model initialization, torch/vLLM compile time, profiling/warmup, and persistent compile/JIT cache classification versus the successful cold-v3 baseline. Do not add a canary call or rerun solely for efficiency evidence.
- Keep C3 synthetic same-modality certification designed but disabled until separately authorized. When used later it must share the same live initialized engine with subsequent domain work and must never consume one of the scientific benchmark's exact three calls.
- After guarded downstream calibration, decide whether to promote Qwen only for the validated residual/question classes while keeping fail-closed Codex/human fallthrough. No production routing or scientific-state materialization occurs before that gate passes.
- Separately retain the unresolved scan/OCR source-selection work: replace the invalid blank scan target with a content-bearing image-only page before any PP-OCRv6 scan-recovery promotion claim.

## Blockers / gates

- PP-OCRv6 remains resource-pass / quality-not-promoted; the blank scan target still requires replacement with a content-bearing image-only scan before scan-recovery promotion can be evaluated.
- PaddleOCR-VL-1.6 is not promoted: it exceeded current resource ceilings and fabricated chart numerics / missed key semantic relations; it remains perception/parser evidence only.
- Qwen3.5-4B is selected as the local VLM family, but unguarded free-text relation output is not production-promoted. The bounded downstream EXTRACT/VERIFY calibration must prove fail-closed relation validation, provenance preservation, and authoritative-PDF Codex fallthrough.
- Codex STANDARD EXTRACT/VERIFY remains the production semantic baseline until the bounded guarded-Qwen downstream calibration demonstrates equivalent grounded evidence/provenance quality.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
