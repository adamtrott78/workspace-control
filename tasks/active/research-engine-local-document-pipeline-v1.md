<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: `research-engine-local-document-pipeline-v1`
- Stage: `residual_escalation_and_local_semantic_fallbacks`
- research-engine remote canonical: `0bded264aa4bb021450b9d62c66555843155ead8`
- research-engine Lambda/local last verified: `d228f8fab477b68a64b911e72e8b2ba2292cf114` clean
- research daemon: keep inactive/dead PID 0
- sustained research: disabled
- STANDARD Codex authoritative-PDF EXTRACT/VERIFY remains production semantic baseline

## PaddleOCR-VL fourth attempt
The model-native direct Transformers path reached GPU allocation but still
executed zero VLM calls.

Uploaded report:
- loader: `AutoModelForCausalLM+AutoProcessor`
- candidate inference calls: 0
- gpu process samples: 4
- peak process VRAM: 2342 MiB
- model init: false
- runtime completed: false
- scientific state materialized: false
- failure:
  `TypeError: create_causal_mask() got an unexpected keyword argument 'inputs_embeds'`

This is an API compatibility defect, not model-quality evidence.

The pinned PaddleOCR-VL-1.6 custom code calls
`transformers.masking_utils.create_causal_mask(..., inputs_embeds=...)`.
Transformers 4.55.0 exposes that argument as singular
`input_embeds`. The mismatch is also reported publicly for PaddleOCR-VL-1.6.

## Causal-mask compatibility hotfix
research-engine PR #76 merged as
`0bded264aa4bb021450b9d62c66555843155ead8`.

- PR-head CI `37176718312`: PASS
- canonical-main CI `37176794527`: PASS

The benchmark now installs a narrow in-memory compatibility function **before**
the pinned custom modeling module loads.

Behavior:
- inspect the installed `create_causal_mask` signature;
- if native `inputs_embeds` exists, no alias is required;
- if Transformers exposes `input_embeds`, translate only
  `inputs_embeds -> input_embeds`;
- fail closed for an unexpected signature;
- reject a call containing both spellings.

No model file or weight is changed. No package is upgraded. The runtime remains:
- Torch 2.8.0
- TorchVision 0.23.0
- Transformers 4.55.0
- protobuf 5.29.5
- direct `AutoModelForCausalLM + AutoProcessor`
- pinned local model only
- `local_files_only=True`
- offline Hub/Transformers environment

The same two validated crops, prompts, three-call budget, resource ceilings,
quality thresholds, daemon policy, Codex requirement, Qwen fallback boundary,
and scientific-state prohibition remain unchanged.

## Next safe action
Keep sustained research disabled and `research-engine-daemon.service`
inactive/dead. Treat remote
`main@0bded264aa4bb021450b9d62c66555843155ead8` as canonical and Lambda/local
`main@d228f8fab477b68a64b911e72e8b2ba2292cf114` as the last verified clean
state.

On Lambda:
1. require branch `main`, clean checkout, daemon inactive/dead PID 0;
2. fetch origin and require `origin/main` exactly
   `0bded264aa4bb021450b9d62c66555843155ead8`;
3. fast-forward only to that commit;
4. rerun `bash deploy/run-paddleocr-vl-residual-benchmark.sh`;
5. return the new visible `OUTPUT_ROOT` plus
   `paddleocr-vl-benchmark-report.json`, or the first hard error.

No dependency rebuild or upgrade is required for this rerun.

Do not start the daemon, invoke Qwen3.5-4B or Codex, change production routing,
or materialize scientific state.

## Remaining work
- Execute the first actual PaddleOCR-VL generations through the patched,
  model-native Transformers path.
- Human-score the outputs against the durable annotated facts.
- If local VLM quality passes, execute the required separate contemporaneous
  STANDARD Codex authoritative-PDF control before promotion.
- If PaddleOCR-VL runs but fails/abstains on quality, open Qwen3.5-4B visual
  fallback only for the failed residual rather than continuing wrapper/runtime
  patching.
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
