<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: `research-engine-local-document-pipeline-v1`
- Stage: `residual_escalation_and_local_semantic_fallbacks`
- research-engine remote canonical: `a3635f817c49dd40613724cca1353487173305d5`
- research-engine Lambda/local last verified: `a5117e4af6082e286942321ecea1b7c5b279b589` clean
- research daemon: keep inactive/dead PID 0
- sustained research: disabled
- STANDARD Codex authoritative-PDF EXTRACT/VERIFY remains production semantic baseline

## Current PaddleOCR-VL status
Two targeted Lambda initialization attempts have occurred, and **neither
executed a VLM inference call**.

### Attempt 1
- missing runtime dependency: `torchvision`
- candidate inference calls: 0
- no quality/resource evidence

PR #73 corrected this by pinning:
- `torch==2.8.0`
- `torchvision==0.23.0`
- `transformers==4.55.0`
- scoped `trust_remote_code=True` for the pinned local model only

### Attempt 2
The exact validated crops rendered correctly:
- Figure 6: expected three-panel CIFAR training/test-error chart
- Figure 3: expected VGG-19 / 34-layer plain / 34-layer residual architecture diagram

Model initialization then stopped because `protobuf` was absent.

Uploaded report:
- candidate inference calls: 0
- runtime_completed: false
- model_init: false
- GPU process samples: 0
- peak process VRAM: 0 MiB
- scientific_state_materialized: false
- measurement_decision: `REJECT_RESOURCE_OR_RUNTIME`

This is a dependency failure only, **not** VLM quality evidence.

## Protobuf hotfix
research-engine PR #74 merged as
`a3635f817c49dd40613724cca1353487173305d5`.

- PR-head CI `37175354021`: PASS
- canonical-main CI `37175428542`: PASS

The isolated VLM runtime now additionally pins:
- `protobuf==5.29.5`

The runtime-ready sentinel now checks:
- Torch 2.8.0
- TorchVision 0.23.0
- Transformers 4.55.0
- protobuf 5.29.5

Therefore the previous incomplete environment is automatically invalidated and
rebuilt before the next inference attempt.

No benchmark source/region, PaddleOCR-VL revision, model checksum, inference
count, resource ceiling, quality threshold, trust scope, daemon policy,
Qwen/Codex boundary, production routing, or scientific-state behavior changed.

## Next safe action
Keep sustained research disabled and `research-engine-daemon.service`
inactive/dead. Treat remote
`main@a3635f817c49dd40613724cca1353487173305d5` as canonical and Lambda/local
`main@a5117e4af6082e286942321ecea1b7c5b279b589` as the last verified clean
state.

On Lambda:
1. require branch `main`, clean checkout, daemon inactive/dead PID 0;
2. fetch origin and require `origin/main` exactly
   `a3635f817c49dd40613724cca1353487173305d5`;
3. fast-forward only to that commit;
4. rerun `bash deploy/run-paddleocr-vl-residual-benchmark.sh`;
5. return the new visible `OUTPUT_ROOT` plus:
   - `paddleocr-vl-benchmark-report.json`
   - `figure6_cifar_training_chart-page-zb7.png`
   - `figure3_network_architecture-page-zb3.png`
   or the first hard error.

Do not use either prior zero-inference report as quality evidence. Do not start
the daemon, invoke Qwen3.5-4B or Codex, change production routing, or
materialize scientific state.

## Remaining work
- Execute the first actual PaddleOCR-VL calls on Lambda.
- Human-score Figure 6 / Figure 3 outputs against the durable annotated facts.
- If local VLM quality passes, execute the required separate contemporaneous
  STANDARD Codex authoritative-PDF control before promotion.
- If PaddleOCR-VL fails or abstains, open Qwen3.5-4B visual fallback only for
  the failed residual.
- Replace the invalid blank scan benchmark with a content-bearing image-only
  scan before reopening PP-OCRv6 scan-recovery quality.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative
capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced
research-engine evidence as the complete handoff. Do not rely on previous chat
state. Follow the capsule's exact `next_safe_action`.
