<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: `research-engine-local-document-pipeline-v1`
- Stage: `residual_escalation_and_local_semantic_fallbacks`
- research-engine remote canonical: `120aa27123111f27fb17a7e7cd7e1139d1a53a54`
- research-engine Lambda/local last verified: `9019be081db373395adeffa28fe515c33e582fb3` clean
- research daemon: keep inactive/dead PID 0
- sustained research: disabled
- STANDARD Codex authoritative-PDF EXTRACT/VERIFY remains production semantic baseline

## PP-OCRv6 measured outcome
The bounded PP-OCRv6 Lambda run completed with all runtime/resource checks PASS:
- exactly 3 candidate inference calls
- failure: null
- model init: 0.7756724039791152 s
- peak process VRAM: 1818 MiB
- peak RSS: 1443.69140625 MiB
- worst warm page: 0.3322868350078352 s

Human review did **not** promote the model:
- zero-based page 3 is visually almost blank. Zero OCR output is appropriate,
  but the target is invalid for demonstrating content-bearing image-only scan
  recovery and must be replaced.
- zero-based page 16 is a genuine low-confidence scanned chart. PP-OCRv6
  recovers most labels, dates, axes and captions, but visible errors include
  HEIGHT (KM) -> HEI (KM), missed/detached small orbit-week digits, fused
  `222`, anomalous `-8-`, and imperfect date/row structure.

The durable hard quality thresholds therefore remain unproven and PP-OCRv6 is
resource-pass / quality-not-promoted. The compact review is:
`benchmarks/document_intelligence/ppocrv6-human-quality-review.v1.json`.

## Targeted PaddleOCR-VL 1.6 gate
research-engine PR #72 merged as
`120aa27123111f27fb17a7e7cd7e1139d1a53a54`.

- PR-head CI `37174205004`: PASS
- canonical-main CI `37174284154`: PASS
- contract:
  `benchmarks/document_intelligence/paddleocr-vl-residual-benchmark-contract.v1.json`
- runner: `deploy/run-paddleocr-vl-residual-benchmark.sh`

The gate uses only the already-prefetched PaddleOCR-VL-1.6 model:
- revision `c5630abae1d940eafe0697512a0325494b02ab42`
- `model.safetensors` SHA-256
  `85a479d506a11e724e7285d395c551be69f41dbc16b6342d3cacfb189aed71db`

Scope is exactly the two accepted ResNet visual regions:
- Figure 6, zero-based page 7, bbox
  `[99.19828033447266,72.1703872680664,495.0450134277344,171.62620544433594]`
- Figure 3, zero-based page 3, bbox
  `[50.5037956237793,76.09317016601562,285.709716796875,618.7928466796875]`

The runner renders those two crops, uses `PaddleOCRVL` with the Transformers
engine, disables layout detection / document orientation / unwarping / queues,
and runs exactly three local VLM calls. PP-DocLayoutV3, Qwen3.5-4B, Codex,
whole-document VLM parsing, daemon start, production routing and scientific
state mutation remain closed.

A resource-successful run yields
`MEASURED_PENDING_HUMAN_AND_CODEX_CONTROL`, not promotion. Human annotated
fact/relation review comes next; only if that passes may the separate required
contemporaneous authoritative-PDF Codex control open.

## Next safe action
Keep sustained research disabled and `research-engine-daemon.service`
inactive/dead. Treat remote
`main@120aa27123111f27fb17a7e7cd7e1139d1a53a54` as canonical and Lambda/local
`main@9019be081db373395adeffa28fe515c33e582fb3` as the last verified clean
state.

On Lambda:
1. require branch `main`, clean checkout, daemon inactive/dead PID 0;
2. fetch origin and require `origin/main` exactly
   `120aa27123111f27fb17a7e7cd7e1139d1a53a54`;
3. fast-forward only to that commit;
4. run `bash deploy/run-paddleocr-vl-residual-benchmark.sh`;
5. return the visible `OUTPUT_ROOT` plus:
   - `paddleocr-vl-benchmark-report.json`
   - `figure6_cifar_training_chart-page-zb7.png`
   - `figure3_network_architecture-page-zb3.png`
   or the first hard error.

Do not start the daemon, invoke Qwen3.5-4B or Codex, change production routing,
or materialize scientific state.

## Remaining work
- Execute the bounded PaddleOCR-VL local visual measurement.
- Human-score Figure 6 / Figure 3 outputs against the durable annotated facts.
- If local VLM quality passes, execute the required separate contemporaneous
  STANDARD Codex authoritative-PDF control before promotion.
- If PaddleOCR-VL fails or abstains, open Qwen3.5-4B visual fallback only for
  the failed residual.
- Replace the invalid blank scan benchmark with a content-bearing image-only
  scan before reopening PP-OCRv6 scan-recovery quality.
- Keep Qwen3.5-4B semantic EXTRACT/VERIFY closed until its separately bounded
  semantic gate opens.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative
capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced
research-engine evidence as the complete handoff. Do not rely on previous chat
state. Follow the capsule's exact `next_safe_action`.
