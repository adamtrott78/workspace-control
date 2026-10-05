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
- Remote checkpoint: 032922019d3602d51312e895691f8c851814aaf7
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: d0debd205de46a608fce5b9a15f3fa0fdd6de4e6
- Local clean: true

## Next safe action

Keep sustained research disabled and research-engine-daemon.service inactive/dead. research-engine canonical main is now 032922019d3602d51312e895691f8c851814aaf7; PR #79 head CI 37247452874 and canonical-main CI 37247584085 both PASS. The benchmark contract and exact validated Figure 6/Figure 3 source regions, prompts, Qwen revision, three-call budget, quality/resource thresholds, provenance requirements, production routing, and scientific-state boundary are unchanged. Lambda/local is still last verified clean at main@d0debd205de46a608fce5b9a15f3fa0fdd6de4e6. First re-inspect that checkout and fast-forward it to 032922019d3602d51312e895691f8c851814aaf7 only if it is still clean on main; do not reset/stash/clean unrelated work. Keep the daemon stopped. Then run exactly `bash deploy/run-qwen35-visual-benchmark.sh`. The corrected runner pins the isolated CUDA-12.9 stack to vLLM 0.30.0+cu129, torch 2.13.0+cu129, and torchcodec 0.15.0+cu129, and it must pass a fail-fast preflight importing torchcodec and the same `from vllm import LLM, SamplingParams` multimodal path plus a real CUDA allocation before any QWEN_CALL_START. If that preflight fails, return the visible OUTPUT_ROOT and first hard error and keep candidate inference at zero. If it passes, allow only the existing three bounded Qwen calls to run and return OUTPUT_ROOT plus qwen35-visual-benchmark-report.json. Do not score prior zero-inference failures, start sustained research, invoke Codex, change benchmark inputs/prompts/thresholds, change production routing, materialize scientific state, or update the host driver unless later evidence requires it.

## Remaining work

- Keep sustained research disabled and research-engine-daemon.service inactive/dead. Under a clean-main preflight, fast-forward the Lambda research-engine checkout from its last verified d0debd205de46a608fce5b9a15f3fa0fdd6de4e6 state to canonical main@032922019d3602d51312e895691f8c851814aaf7; do not reset, stash, clean, or overwrite unrelated work.
- Run the exact existing `bash deploy/run-qwen35-visual-benchmark.sh`. The runner must reconcile the isolated runtime to vLLM 0.30.0+cu129 / torch 2.13.0+cu129 / torchcodec 0.15.0+cu129 and pass the full torchcodec + `from vllm import LLM, SamplingParams` multimodal import plus real CUDA allocation preflight before any Qwen call.
- If the runtime fails before QWEN_CALL_START, return the visible OUTPUT_ROOT and first hard error, keep candidate inference at zero, and do not draw a Qwen quality or resource conclusion.
- Do not update the host NVIDIA driver unless later evidence establishes that the explicit CUDA-12.9 runtime still requires a host change.
- If exactly three Qwen calls complete, score Figure 6 panel/model sets, line-style semantics, plain-110 absence, empty curve_numeric_estimates, and zero fabricated facts; score Figure 3 architecture columns, shortcut presence/relations, channel widths, caption FLOPs, and zero fabricated facts.
- Analyze Qwen quality separately from resource-policy outcome. If visual quality passes, run the separate contemporaneous authoritative-PDF Codex control before any promotion.
- Only after visual-control success should bounded local Qwen EXTRACT/VERIFY calibration open.

## Blockers / gates

- PP-OCRv6 remains resource-pass / quality-not-promoted; the blank scan target still requires replacement with a content-bearing image-only scan before scan-recovery promotion can be evaluated.
- PaddleOCR-VL-1.6 direct element-level inference completed but is not promoted: it exceeded current VRAM/latency ceilings and, more importantly, fabricated chart numerics and failed key panel/shortcut relations. It remains perception/parser evidence only.
- Qwen3.5-4B visual-semantic model quality is still unmeasured: all prior Lambda attempts stopped before QWEN_CALL_START, so candidate inference remains zero.
- The isolated CUDA-12.9 runtime repair is merged and CI-validated on research-engine main@032922019d3602d51312e895691f8c851814aaf7, but it has not yet been synchronized to or executed on Lambda. Lambda/local remains last verified clean at main@d0debd205de46a608fce5b9a15f3fa0fdd6de4e6.
- The historical default-vLLM CUDA-13 failure and torchcodec/libnvrtc.so.13 failure remain runtime compatibility evidence only; neither is Qwen model-quality evidence.
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
