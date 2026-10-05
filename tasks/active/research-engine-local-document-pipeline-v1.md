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
- Remote checkpoint: a3d80e9329e231889b11430f98c0de342349fe1f
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 58305fe7484a15ee2ad4f20c91d2e4f4aa477b9f
- Local clean: true

## Next safe action

Keep sustained research disabled and research-engine-daemon.service inactive/dead. research-engine canonical main is now a3d80e9329e231889b11430f98c0de342349fe1f; PR #81 head CI 37252103851 and canonical-main CI 37252231096 both PASS. The benchmark contract and exact validated Figure 6/Figure 3 source regions, prompts, Qwen revision, three-call budget, sampling parameters, quality/resource thresholds, provenance requirements, production routing, Codex-control boundary, and scientific-state boundary are unchanged. Lambda/local ended the last attempt on clean main@58305fe7484a15ee2ad4f20c91d2e4f4aa477b9f with research-engine-daemon.service inactive/dead. That run passed host/build compatibility, exact TorchCodec/vLLM multimodal import/native-library smoke, and a real CUDA allocation, then failed before QWEN_MODEL_INIT_COMPLETE/QWEN_CALL_START because vLLM's default FlashInfer top-k/top-p sampler attempted JIT compilation and could not find nvcc or /usr/local/cuda. Candidate inference remains zero. First re-inspect the clean Lambda checkout and fast-forward only from 58305fe7484a15ee2ad4f20c91d2e4f4aa477b9f to a3d80e9329e231889b11430f98c0de342349fe1f; do not reset/stash/clean unrelated work. Then run exactly `bash deploy/run-qwen35-visual-benchmark.sh`. The corrected runner sets VLLM_USE_FLASHINFER_SAMPLER=0, records the vLLM-native sampler in runtime identity v3, preserves the existing cu129 package environment, uses a persistent contract/model-keyed vLLM compile cache, and should verify/reuse the two existing crop-cache entries. If initialization fails before QWEN_CALL_START, return OUTPUT_ROOT, qwen35-benchmark-receipt.json, qwen35-visual-benchmark-report.json if present, and only the first hard helper-log excerpt. If initialization passes, allow only the existing three bounded Qwen calls and return the compact receipt plus primary report. Do not invoke Codex yet, start sustained research, change scientific inputs/prompts/sampling/thresholds, change production routing, materialize scientific state, install a host CUDA toolkit merely to satisfy FlashInfer, or update the NVIDIA driver unless later evidence requires it.

## Remaining work

- Keep sustained research disabled and research-engine-daemon.service inactive/dead. Re-inspect the Lambda research-engine checkout and fast-forward from its last verified clean main@58305fe7484a15ee2ad4f20c91d2e4f4aa477b9f state to canonical main@a3d80e9329e231889b11430f98c0de342349fe1f only if it is still clean on main; do not reset, stash, clean, or overwrite unrelated work.
- Run exactly `bash deploy/run-qwen35-visual-benchmark.sh`. The corrected runner must reuse the existing package environment without package reconstruction, revalidate runtime contract v3 with VLLM_USE_FLASHINFER_SAMPLER=0, use the vLLM-native sampler, and keep the daemon stopped.
- The next natural run should verify the existing Figure 6/Figure 3 content-addressed cache rather than rerender: expected cache identities are already populated from the prior run. Do not rerun solely to manufacture cache evidence; this retry is required by the owning Qwen task.
- The persistent vLLM compile cache starts under the new runtime-contract/model-revision key. Measure compile/profile behavior on this required retry and any later natural retry; do not copy old timestamp-scoped compile artifacts into the new cache without an explicit compatibility contract.
- If engine initialization still fails before QWEN_CALL_START, return the compact receipt, primary report if created, and only the targeted helper-log excerpt containing the first hard root cause. Candidate inference remains zero and no semantic-quality conclusion is permitted.
- If exactly three Qwen calls complete, score Figure 6 panel/model sets, line-style semantics, plain-110 absence, empty curve_numeric_estimates, and zero fabricated facts; score Figure 3 architecture columns, shortcut presence/relations, channel widths, caption FLOPs, and zero fabricated facts.
- Analyze semantic quality separately from resource-policy outcome. Only if visual quality passes may the separate contemporaneous authoritative-PDF Codex control open before any promotion.
- Do not update the host NVIDIA driver or install a system CUDA toolkit/nvcc merely for this benchmark unless later evidence establishes that the selected native-sampler CUDA-12.9 path genuinely requires it.

## Blockers / gates

- PP-OCRv6 remains resource-pass / quality-not-promoted; the blank scan target still requires replacement with a content-bearing image-only scan before scan-recovery promotion can be evaluated.
- PaddleOCR-VL-1.6 direct element-level inference completed but is not promoted: it exceeded current VRAM/latency ceilings and, more importantly, fabricated chart numerics and failed key panel/shortcut relations. It remains perception/parser evidence only.
- Qwen3.5-4B visual-semantic model quality is still unmeasured: every Lambda attempt so far stopped before QWEN_CALL_START, so candidate inference remains zero.
- Latest Lambda run on main@58305fe7484a15ee2ad4f20c91d2e4f4aa477b9f passed host/build, TorchCodec/vLLM import/native-library, and real CUDA-allocation smoke, then failed during vLLM engine initialization because the default FlashInfer sampler attempted JIT compilation without nvcc. This is runtime-startup evidence only, not Qwen quality evidence.
- Native-sampler/persistent-compile-cache repair is merged and CI-validated on research-engine main@a3d80e9329e231889b11430f98c0de342349fe1f but has not yet been executed on Lambda. Lambda/local ended the prior failed run clean at main@58305fe7484a15ee2ad4f20c91d2e4f4aa477b9f with the daemon inactive/dead.
- Historical CUDA-13/default-vLLM, libnvrtc.so.13, and TorchCodec-0.15 FFmpeg/libav failures remain runtime compatibility evidence only and are not Qwen model-quality evidence.
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
