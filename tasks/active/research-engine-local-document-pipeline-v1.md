<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## State
- Task: `research-engine-local-document-pipeline-v1`
- Stage: `residual_escalation_and_local_semantic_fallbacks`
- research-engine remote canonical: `d0debd205de46a608fce5b9a15f3fa0fdd6de4e6`
- research-engine Lambda/local verified head: `d0debd205de46a608fce5b9a15f3fa0fdd6de4e6`
- research-engine Lambda checkout was clean before the bounded runtime attempt
- research daemon: keep inactive/dead PID 0
- sustained research: disabled
- STANDARD Codex authoritative-PDF EXTRACT/VERIFY remains production semantic baseline

## Prior candidate outcomes

### PP-OCRv6
Resource/latency PASS but quality not promoted. The content-bearing chart improved
substantially over native text but retained visible OCR errors, and the original
image-only scan target proved nearly blank and must be replaced before scan
recovery can be adjudicated.

### PaddleOCR-VL-1.6
Three calls completed, but direct element-level inference was not promoted:
- model init: 1.4238369059967226 s
- Figure 6: 72.534 s first / 72.997 s repeat
- Figure 3: 108.519 s
- peak process VRAM: 19,956 MiB
- peak RSS: 2802.21 MiB

Figure 6 recovered useful model labels but fabricated unsupported numeric table
values and collapsed panel relations. Figure 3 recovered many visible labels
but did not preserve the shortcut topology. PaddleOCR-VL remains useful
perception/parser evidence, not semantic authority.

## Qwen3.5-4B targeted visual-semantic gate

research-engine PR #78 merged as:
`d0debd205de46a608fce5b9a15f3fa0fdd6de4e6`

- PR-head CI `37242434658`: PASS
- canonical-main CI `37242540771`: PASS
- contract:
  `benchmarks/document_intelligence/qwen35-visual-benchmark-contract.v1.json`
- runner:
  `deploy/run-qwen35-visual-benchmark.sh`

The gate uses:
- model: `Qwen/Qwen3.5-4B`
- revision: `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- exact pinned two-shard safetensor checksums
- exactly three intended calls: Figure 6 cold, Figure 3 warm, Figure 6 repeat
- structured evidence prompts
- zero fabricated-fact tolerance
- no Codex during the initial local gate
- no daemon start, production routing change, or scientific-state materialization

## Lambda runtime attempts

### Attempt 1: default vLLM 0.30.0 runtime

The first Lambda run used the default vLLM 0.30.0 installation path.

Result:
`BLOCKED_DRIVER_CUDA13_ZERO_INFERENCE`

Observed:
- `HEAD=d0debd205de46a608fce5b9a15f3fa0fdd6de4e6`
- scientific state remained false
- GPU 0 / RTX A4500 selected
- exact Figure 6 and Figure 3 crops rendered successfully
- CUDA allocation preflight failed before Qwen inference
- Torch reported NVIDIA driver API version `12080` was too old for the installed CUDA-13 runtime
- no `QWEN_CALL_START`
- zero Qwen inference calls
- no Qwen quality result

This was classified strictly as runtime-binary/driver compatibility evidence.

### Attempt 2: isolated CUDA-12.9 rebuild

The failed Qwen runtime was rebuilt with:
- `vLLM 0.30.0` CUDA-12.9 build
- `torch 2.13.0+cu129`
- Torch CUDA runtime 12.9

CUDA preflight result:

```text
cuda_allocation_probe=PASS
cuda_device_name=NVIDIA RTX A4500
torch=2.13.0+cu129
torch_cuda_runtime=12.9
vllm=0.30.0
vllm_cuda_build=cu129
```

This establishes that the existing host driver is capable of the CUDA-12.9
Torch allocation path.

### Attempt 3: Qwen benchmark with CUDA-12.9 runtime

The exact existing benchmark was resumed.

Visible output root:
`/home/atrott/adamArchives/Adam/workspace-control-tmp/qwen35-visual-benchmark-20261005T000739Z`

Observed pre-inference state:
- `HEAD=d0debd205de46a608fce5b9a15f3fa0fdd6de4e6`
- `SCIENTIFIC_STATE_MATERIALIZED=false`
- selected GPU 0 / RTX A4500
- free GPU memory: 20,037 MiB
- baseline GPU usage: 18 MiB
- authoritative PDF resolved from the previously validated source audit
- CUDA-12.9 allocation preflight passed again

Validated rerendered targets:

Figure 6:
- page index 7
- 1650 x 414 px
- bbox:
  `[99.19828033447266,72.1703872680664,495.0450134277344,171.62620544433594]`

Figure 3:
- page index 3
- 980 x 2261 px
- bbox:
  `[50.5037956237793,76.09317016601562,285.709716796875,618.7928466796875]`

The benchmark then failed before the first Qwen call while importing the vLLM
multimodal stack.

Terminal cause:

```text
OSError: libnvrtc.so.13: cannot open shared object file: No such file or directory
```

The dependency chain reached:

```text
vllm
  -> multimodal
  -> torchcodec
  -> torchcodec/libtorchcodec_image.so
  -> libnvrtc.so.13
```

Final classification:
`BLOCKED_TORCHCODEC_NVRTC13_ZERO_INFERENCE`

Important:
- the Torch CUDA-12.9 allocation path itself passed
- the failure occurs later during full vLLM import
- no `QWEN_CALL_START` occurred
- candidate inference count remains zero
- no Qwen model-quality conclusion is permitted
- no Qwen latency/VRAM/process-tree RSS benchmark result exists yet
- scientific state remained unmaterialized

## Current blocker

The active blocker is the isolated Qwen runtime/dependency composition:
the CUDA-12.9 Torch allocation path works, but importing the full vLLM
multimodal path loads `torchcodec/libtorchcodec_image.so`, which requires
unavailable `libnvrtc.so.13`.

This is runtime/dependency evidence only, not Qwen quality evidence.

## Next safe action

Keep sustained research disabled and
`research-engine-daemon.service` inactive/dead.

Continue from research-engine:
`main@d0debd205de46a608fce5b9a15f3fa0fdd6de4e6`

Preserve the existing Qwen3.5-4B benchmark contract, model revision, source PDF,
Figure 6/Figure 3 bboxes, prompts, inference count, quality thresholds, daemon
policy, production-routing boundary, and scientific-state boundary.

First diagnose and correct only the isolated runtime/dependency compatibility
problem that causes the full vLLM multimodal import to require
`libnvrtc.so.13`, despite the already-passing CUDA-12.9 Torch allocation path.

Before another three-call benchmark attempt, add or execute a fail-fast
preflight that imports the same vLLM multimodal path used by
`run_qwen35_visual_benchmark.py`, not merely `torch.cuda`.

Do not:
- score Qwen from the zero-inference failures;
- update the host driver merely because the already-bypassed default CUDA-13
  runtime failed;
- change benchmark inputs/prompts/thresholds;
- start the daemon;
- invoke Codex during this initial local gate;
- change production routing;
- materialize scientific state.

Once the full vLLM import/runtime preflight passes, rerun:

```bash
bash deploy/run-qwen35-visual-benchmark.sh
```

Return the visible `OUTPUT_ROOT` plus
`qwen35-visual-benchmark-report.json`, or the first hard error.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal `workspace-control` root route.

Treat the authoritative task capsule, synchronized Markdown handoff, exact
durable Git/runtime state, and referenced research-engine evidence as the
complete handoff.

Do not rely on previous conversation state or another chat's prose summary.

Follow the capsule's exact `next_safe_action`.

Important current runtime state:
- research-engine canonical/local head is
  `d0debd205de46a608fce5b9a15f3fa0fdd6de4e6`;
- the CUDA-12.9 Qwen runtime preflight passes with
  `torch 2.13.0+cu129` / CUDA runtime 12.9 / vLLM 0.30.0 on the RTX A4500;
- the benchmark still has zero Qwen inference calls because importing vLLM's
  multimodal path loads `torchcodec/libtorchcodec_image.so`, which fails on
  missing `libnvrtc.so.13`;
- this is runtime/dependency compatibility evidence only, not Qwen quality
  evidence.

Resume by diagnosing that exact blocker while preserving the existing bounded
Qwen benchmark and all fail-closed boundaries.
