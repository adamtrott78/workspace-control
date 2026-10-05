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
- Remote checkpoint: 58305fe7484a15ee2ad4f20c91d2e4f4aa477b9f
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 032922019d3602d51312e895691f8c851814aaf7
- Local clean: true

## Next safe action

Keep sustained research disabled and research-engine-daemon.service inactive/dead. research-engine canonical main is now 58305fe7484a15ee2ad4f20c91d2e4f4aa477b9f; PR #80 head CI 37249925495 and canonical-main CI 37250069412 both PASS. The benchmark contract and exact validated Figure 6/Figure 3 source regions, prompts, Qwen revision, three-call budget, quality/resource thresholds, provenance requirements, production routing, Codex-control boundary, and scientific-state boundary are unchanged. Lambda/local is last verified clean on main@032922019d3602d51312e895691f8c851814aaf7, where the exact execution-path preflight failed before QWEN_CALL_START because TorchCodec 0.15.0+cu129 attempted to load unavailable FFmpeg/libav shared libraries; candidate inference remains zero. First re-inspect that checkout and fast-forward it to 58305fe7484a15ee2ad4f20c91d2e4f4aa477b9f only if it is still clean on main; do not reset/stash/clean unrelated work. Keep the daemon stopped. Then run exactly `bash deploy/run-qwen35-visual-benchmark.sh`. The corrected runner pins the PNG-only path to TorchCodec 0.16.0+cu129 and orders host/build compatibility -> exact runtime/wheel identity/cache -> exact TorchCodec/vLLM multimodal native import -> real CUDA allocation before model hashing/rendering/inference. If preflight fails before QWEN_CALL_START, return OUTPUT_ROOT plus qwen35-benchmark-receipt.json and the targeted qwen35-runtime-preflight.log excerpt; keep candidate inference at zero and draw no Qwen quality/resource conclusion. If it passes, allow only the existing three bounded Qwen calls and return OUTPUT_ROOT, qwen35-benchmark-receipt.json, and qwen35-visual-benchmark-report.json. Do not invoke Codex yet, rerun inference only for efficiency measurement, start sustained research, change benchmark inputs/prompts/thresholds, change production routing, materialize scientific state, or update the host driver unless later evidence requires it.

## Remaining work

- Keep sustained research disabled and research-engine-daemon.service inactive/dead. Re-inspect the Lambda research-engine checkout and fast-forward from its last verified clean main@032922019d3602d51312e895691f8c851814aaf7 state to canonical main@58305fe7484a15ee2ad4f20c91d2e4f4aa477b9f only if it is still clean on main; do not reset, stash, clean, or overwrite unrelated work.
- Run exactly `bash deploy/run-qwen35-visual-benchmark.sh`. The corrected runner must establish host/build compatibility, reconcile/verify the exact cu129 runtime identity, pass the same TorchCodec + `from vllm import LLM, SamplingParams` execution-path smoke and a real CUDA allocation before model hashing, deterministic render materialization, or Qwen inference.
- On the next natural run the expected existing runtime should require only the TorchCodec 0.15.0+cu129 -> 0.16.0+cu129 repair if all other exact identities still match; do not rebuild the venv merely to manufacture cache evidence.
- If preflight fails before QWEN_CALL_START, return the visible OUTPUT_ROOT, qwen35-benchmark-receipt.json, and only the targeted qwen35-runtime-preflight.log excerpt needed to diagnose the hard error. Candidate inference remains zero and no Qwen quality/resource conclusion is permitted.
- If the preflight passes, allow only the existing three Qwen calls. Return OUTPUT_ROOT, qwen35-benchmark-receipt.json, and qwen35-visual-benchmark-report.json.
- If exactly three calls complete, score Figure 6 panel/model sets, line-style semantics, plain-110 absence, empty curve_numeric_estimates, and zero fabricated facts; score Figure 3 architecture columns, shortcut presence/relations, channel widths, caption FLOPs, and zero fabricated facts.
- Analyze semantic quality separately from resource-policy outcome. Only if visual quality passes may the separate contemporaneous authoritative-PDF Codex control open before any promotion.
- Do not rerun three Qwen calls merely to manufacture Wave-2 cache-hit evidence; measure exact runtime/render reuse on a later natural retry or an inference-free cache verification gate.
- Do not update the host NVIDIA driver unless later evidence establishes that the explicit CUDA-12.9 runtime still requires a host change.

## Blockers / gates

- PP-OCRv6 remains resource-pass / quality-not-promoted; the blank scan target still requires replacement with a content-bearing image-only scan before scan-recovery promotion can be evaluated.
- PaddleOCR-VL-1.6 direct element-level inference completed but is not promoted: it exceeded current VRAM/latency ceilings and, more importantly, fabricated chart numerics and failed key panel/shortcut relations. It remains perception/parser evidence only.
- Qwen3.5-4B visual-semantic model quality is still unmeasured: every Lambda attempt so far stopped before QWEN_CALL_START, so candidate inference remains zero.
- The newest runtime repair is merged and fully CI-validated on research-engine main@58305fe7484a15ee2ad4f20c91d2e4f4aa477b9f, but that exact commit has not yet been executed on Lambda. Lambda/local is last verified clean at main@032922019d3602d51312e895691f8c851814aaf7.
- The latest concrete Lambda blocker was TorchCodec 0.15.0+cu129 eagerly loading absent FFmpeg/libav shared libraries. PR #80 moves the PNG-only path to TorchCodec 0.16.0+cu129 and must now be proven by the exact Lambda execution-path smoke; this is runtime compatibility evidence only.
- Historical CUDA-13/default-vLLM and libnvrtc.so.13 failures likewise remain runtime compatibility evidence only and are not Qwen model-quality evidence.
- A broader local semantic replacement for routine EXTRACT/VERIFY remains unopened until Qwen's visual-semantic benchmark is actually executed and adjudicated.
- Codex STANDARD EXTRACT/VERIFY remains the production semantic baseline until bounded local controls demonstrate equivalent evidence/provenance quality.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
