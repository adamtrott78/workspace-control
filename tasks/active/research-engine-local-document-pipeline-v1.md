<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: `research-engine-local-document-pipeline-v1`
- Stage: `residual_escalation_and_local_semantic_fallbacks`
- research-engine remote canonical: `d228f8fab477b68a64b911e72e8b2ba2292cf114`
- research-engine Lambda/local last verified: `a3635f817c49dd40613724cca1353487173305d5` clean
- research daemon: keep inactive/dead PID 0
- sustained research: disabled
- STANDARD Codex authoritative-PDF EXTRACT/VERIFY remains production semantic baseline

## PaddleOCR-VL initialization history
Three Lambda attempts have occurred and **all three executed zero VLM calls**.

1. Missing `torchvision`.
2. Missing `protobuf`.
3. All dependencies present, but PaddleX 3.7's Transformers wrapper requested
   `AutoModelForImageTextToText` for the pinned custom
   `PaddleOCRVLConfig`. The model's own `config.json` declares
   `AutoModel` and `AutoModelForCausalLM`, not
   `AutoModelForImageTextToText`, so Transformers 4.55.0 rejected the
   wrapper before weight initialization.

The third uploaded report records:
- candidate inference calls: 0
- runtime_completed: false
- model_init: false
- gpu process samples: 0
- peak process VRAM: 0 MiB
- scientific_state_materialized: false
- measurement_decision: `REJECT_RESOURCE_OR_RUNTIME`

This is a wrapper-interface incompatibility, not model-quality evidence.

## Direct model-native Transformers hotfix
research-engine PR #75 merged as
`d228f8fab477b68a64b911e72e8b2ba2292cf114`.

- corrected PR-head CI `37176034391`: PASS
- canonical-main CI `37176117264`: PASS

The benchmark now bypasses only the incompatible PaddleX Transformers wrapper.
It does **not** modify model files or weights.

The exact checksum-pinned local PaddleOCR-VL-1.6 artifact is loaded via:
- `AutoProcessor.from_pretrained(..., trust_remote_code=True, local_files_only=True)`
- `AutoModelForCausalLM.from_pretrained(..., trust_remote_code=True, local_files_only=True)`

This matches the auto-class mappings declared by the pinned model itself.

The runtime remains:
- Torch 2.8.0
- TorchVision 0.23.0
- Transformers 4.55.0
- protobuf 5.29.5
- offline model lookup only
- one selected GPU
- daemon stopped
- no scientific-state mutation

The two benchmark regions and three-call budget are unchanged:
1. Figure 6 with model-native `Chart Recognition:`
2. Figure 3 with model-native `OCR:`
3. Figure 6 warm repeat with `Chart Recognition:`

If these model-native tasks run but fail to recover the required chart facts or
architecture relationships, that is a legitimate PaddleOCR-VL capability miss.
Do not resume PaddleX-wrapper patching; open the selected Qwen visual fallback
for the failed visual residual instead.

## Next safe action
Keep sustained research disabled and `research-engine-daemon.service`
inactive/dead. Treat remote
`main@d228f8fab477b68a64b911e72e8b2ba2292cf114` as canonical and Lambda/local
`main@a3635f817c49dd40613724cca1353487173305d5` as the last verified clean
state.

On Lambda:
1. require branch `main`, clean checkout, daemon inactive/dead PID 0;
2. fetch origin and require `origin/main` exactly
   `d228f8fab477b68a64b911e72e8b2ba2292cf114`;
3. fast-forward only to that commit;
4. rerun `bash deploy/run-paddleocr-vl-residual-benchmark.sh`;
5. return the new visible `OUTPUT_ROOT` plus
   `paddleocr-vl-benchmark-report.json`, or the first hard error.

Existing Figure 6 / Figure 3 crop images are already visually validated and may
be reused unless the rerender differs.

Do not start the daemon, invoke Qwen3.5-4B or Codex, change production routing,
or materialize scientific state.

## Remaining work
- Execute the first actual PaddleOCR-VL generations through the model-native
  direct Transformers interface.
- Human-score the outputs against the durable annotated facts.
- If local VLM quality passes, run the required separate contemporaneous
  STANDARD Codex authoritative-PDF control before promotion.
- If PaddleOCR-VL runs but fails/abstains, open Qwen3.5-4B visual fallback only
  for the failed residual.
- Replace the invalid blank scan benchmark before reopening PP-OCRv6
  scan-recovery quality.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative
capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced
research-engine evidence as the complete handoff. Do not rely on previous chat
state. Follow the capsule's exact `next_safe_action`.
