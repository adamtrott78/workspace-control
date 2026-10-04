<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: `research-engine-local-document-pipeline-v1`
- Stage: `residual_escalation_and_local_semantic_fallbacks`
- research-engine remote canonical: `9019be081db373395adeffa28fe515c33e582fb3`
- research-engine Lambda/local last verified: `320bfd037ce51dee63dc1ec4bb0e7d5d984d2c5c` clean
- research daemon: keep inactive/dead PID 0
- sustained research: disabled
- Codex STANDARD authoritative-PDF EXTRACT/VERIFY remains production semantic baseline

## Residual model-prefetch PASS
The bounded model-prefetch report passed with zero candidate inference and no
scientific-state materialization.

Pinned PP-OCRv6 artifacts:
- detection: `PaddlePaddle/PP-OCRv6_medium_det@8e0f56fb2ef86b461d99cfc7ac5c137738985f61`
  - Apache-2.0
  - `inference.pdiparams` SHA-256
    `85218d2e3d98f5a21c58b4220627be923a97aee5db3cc71f39536ab31ac53960`
- recognition: `PaddlePaddle/PP-OCRv6_medium_rec@e5a92bcbc5cc1b494628e458d267778f0704fd7c`
  - Apache-2.0
  - `inference.pdiparams` SHA-256
    `1b01c79a914587933f615569e75de54f2e638ebb5d3f3b3c1b38c24ede8c7319`

Other prefetched candidates remain pinned:
- PaddleOCR-VL-1.6:
  `c5630abae1d940eafe0697512a0325494b02ab42`, 1,930,462,423 bytes,
  offline reopen PASS.
- Qwen3.5-4B:
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, 9,342,907,469 bytes,
  offline reopen PASS.

Uploaded model-prefetch report SHA-256:
`a2f68c2b50a4fe416f825e369f9d85887ae295611540f5c06200c509807e3ca3`.

## PP-OCRv6 measurement gate
research-engine PR #71 merged as
`9019be081db373395adeffa28fe515c33e582fb3`.

- final PR-head CI `37172948330`: PASS
- canonical-main CI `37173031391`: PASS
- contract:
  `benchmarks/document_intelligence/ppocrv6-residual-benchmark-contract.v1.json`
- runner: `deploy/run-ppocrv6-residual-benchmark.sh`

This is the first candidate-model inference gate. It:
- constructs one transactional isolated PaddlePaddle 3.2.0 / PaddleOCR 3.7.0
  runtime;
- verifies the prefetched PP-OCRv6 detection/recognition hashes;
- renders only page indices 3 and 16 from the pinned authoritative NASA PDF at
  200 DPI;
- performs exactly three OCR calls: first scan target, warm low-confidence
  target, warm repeat of the scan target;
- measures model initialization, warm-page latency, process GPU VRAM, and peak
  RSS;
- saves OCR text/scores/boxes plus the two page PNGs under visible
  `workspace-control-tmp`.

Resource success is intentionally
`MEASURED_PENDING_HUMAN_QUALITY`, not promotion. The two rendered pages and
OCR results must be reviewed for visible-text coverage, fabricated text, and
page provenance before PP-OCRv6 can suppress a higher tier.

PaddleOCR-VL-1.6, Qwen3.5-4B, Codex, production routing, and scientific-state
writes remain closed in this gate.

## Next safe action
Keep sustained research disabled and `research-engine-daemon.service`
inactive/dead. Treat research-engine remote
`main@9019be081db373395adeffa28fe515c33e582fb3` as canonical and Lambda/local
`main@320bfd037ce51dee63dc1ec4bb0e7d5d984d2c5c` as the last verified local
state.

On Lambda:
1. require branch `main`, clean checkout, daemon inactive/dead PID 0;
2. fetch origin and require `origin/main` exactly
   `9019be081db373395adeffa28fe515c33e582fb3`;
3. fast-forward only to that commit;
4. run `bash deploy/run-ppocrv6-residual-benchmark.sh`;
5. return the visible `OUTPUT_ROOT` plus:
   - `ppocrv6-benchmark-report.json`
   - `scan_textless-page-zb3.png`
   - `low_confidence_text-page-zb16.png`
   or the first hard failure.

Do not send the full console log.

## Remaining work
- Execute and human-review the PP-OCRv6 scan/text measurement.
- Record scan/text promotion or fail-through decision.
- Then open PaddleOCR-VL-1.6 only on validated semantic-visual / exhausted
  structural residuals.
- Open Qwen3.5-4B semantic EXTRACT/VERIFY only on bounded authoritative-PDF
  inputs with contemporaneous STANDARD Codex controls.
- Qwen visual use remains fallback-only after PaddleOCR-VL failure/abstention.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative
capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced
research-engine evidence as the complete handoff. Do not rely on previous chat
state. Follow the capsule's exact `next_safe_action`.
