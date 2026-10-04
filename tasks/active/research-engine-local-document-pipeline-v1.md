<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: `research-engine-local-document-pipeline-v1`
- Stage: `residual_escalation_and_local_semantic_fallbacks`
- research-engine remote canonical: `a5117e4af6082e286942321ecea1b7c5b279b589`
- research-engine Lambda/local last verified: `120aa27123111f27fb17a7e7cd7e1139d1a53a54` clean
- research daemon: keep inactive/dead PID 0
- sustained research: disabled
- STANDARD Codex authoritative-PDF EXTRACT/VERIFY remains production semantic baseline

## PP-OCRv6 outcome
PP-OCRv6 remains resource-pass / quality-not-promoted. The content-bearing chart
was materially improved but did not establish the hard OCR quality thresholds,
and the scan/textless target proved visually almost blank and must be replaced
before scan-recovery quality can be evaluated.

## First PaddleOCR-VL attempt
The first targeted PaddleOCR-VL Lambda attempt did **not** execute the VLM.

At research-engine `main@120aa27123111f27fb17a7e7cd7e1139d1a53a54`:
- the pinned local PaddleOCR-VL-1.6 custom Transformers code requested trust;
- the operator approved it interactively;
- model initialization then failed because `torchvision` was absent;
- candidate inference calls: 0;
- model init: null;
- peak process VRAM: 0 MiB;
- no visual quality evidence was produced.

The resulting `REJECT_RESOURCE_OR_RUNTIME` is an initialization/runtime
failure only, not a PaddleOCR-VL quality rejection.

## Runtime hotfix
research-engine PR #73 merged as
`a5117e4af6082e286942321ecea1b7c5b279b589`.

- PR-head CI `37174690298`: PASS
- canonical-main CI `37174751650`: PASS

The corrected isolated runtime:
- pins `torch==2.8.0`;
- pins matching `torchvision==0.23.0`;
- uses the CUDA 12.6 PyTorch wheel index;
- keeps `transformers==4.55.0`;
- passes `engine_config={"trust_remote_code": True}` only for the already
  prefetched, checksum-verified local PaddleOCR-VL-1.6 model;
- validates Torch/TorchVision/Transformers before accepting the runtime-ready
  sentinel;
- automatically invalidates and rebuilds the incomplete prior venv.

No benchmark regions, inference-call count, resource ceilings, quality
thresholds, daemon policy, Qwen/Codex policy, production routing, or scientific
state behavior changed.

## Next safe action
Keep sustained research disabled and `research-engine-daemon.service`
inactive/dead. Treat remote
`main@a5117e4af6082e286942321ecea1b7c5b279b589` as canonical and Lambda/local
`main@120aa27123111f27fb17a7e7cd7e1139d1a53a54` as the last verified clean
state.

On Lambda:
1. require branch `main`, clean checkout, daemon inactive/dead PID 0;
2. fetch origin and require `origin/main` exactly
   `a5117e4af6082e286942321ecea1b7c5b279b589`;
3. fast-forward only to that commit;
4. rerun `bash deploy/run-paddleocr-vl-residual-benchmark.sh`;
5. return the new visible `OUTPUT_ROOT` plus:
   - `paddleocr-vl-benchmark-report.json`
   - `figure6_cifar_training_chart-page-zb7.png`
   - `figure3_network_architecture-page-zb3.png`
   or the first hard error.

The failed zero-inference report is diagnostic evidence only and must not be
used for quality scoring.

Do not start the daemon, invoke Qwen3.5-4B or Codex, change production routing,
or materialize scientific state.

## Remaining work
- Rerun the targeted PaddleOCR-VL gate on the corrected runtime.
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
