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

## Model prefetch PASS
The bounded model artifact prefetch completed successfully:
- decision: `PASS`
- candidate model inference calls: 0
- scientific state materialized: false
- uploaded report SHA-256:
  `a2f68c2b50a4fe416f825e369f9d85887ae295611540f5c06200c509807e3ca3`

Pinned artifacts:
- PP-OCRv6 medium detection:
  - revision `8e0f56fb2ef86b461d99cfc7ac5c137738985f61`
  - Apache-2.0
  - offline reopen PASS
  - `inference.pdiparams` SHA-256
    `85218d2e3d98f5a21c58b4220627be923a97aee5db3cc71f39536ab31ac53960`
- PP-OCRv6 medium recognition:
  - revision `e5a92bcbc5cc1b494628e458d267778f0704fd7c`
  - Apache-2.0
  - offline reopen PASS
  - `inference.pdiparams` SHA-256
    `1b01c79a914587933f615569e75de54f2e638ebb5d3f3b3c1b38c24ede8c7319`
- PaddleOCR-VL-1.6:
  - revision `c5630abae1d940eafe0697512a0325494b02ab42`
  - Apache-2.0
  - offline reopen PASS
- Qwen3.5-4B:
  - revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
  - Apache-2.0
  - offline reopen PASS

## PP-OCRv6 benchmark gate
research-engine PR #71 merged as
`9019be081db373395adeffa28fe515c33e582fb3`.

- PR-head CI `37172948330`: PASS
- canonical-main CI `37173031391`: PASS
- benchmark contract:
  `benchmarks/document_intelligence/ppocrv6-residual-benchmark-contract.v1.json`
- runner: `deploy/run-ppocrv6-residual-benchmark.sh`

The gate:
- constructs an isolated PaddlePaddle 3.2.0 / PaddleOCR 3.7.0 runtime;
- verifies the exact prefetched PP-OCRv6 det/rec weight checksums;
- renders only the two promoted authoritative NASA pages:
  - zero-based page 3: scan/textless residual
  - zero-based page 16: low-confidence text residual
- runs exactly three OCR calls:
  1. page 3 first/cold
  2. page 16 warm
  3. page 3 warm repeat
- records model-init time, warm-page latency, process GPU memory, peak RSS,
  recognized text/scores/boxes, runtime freeze, and rendered review PNGs;
- keeps PaddleOCR-VL, Qwen, Codex, production routing, and scientific-state
  mutation closed.

Resource success is **not promotion**. Successful execution yields
`MEASURED_PENDING_HUMAN_QUALITY`; the OCR output must be reviewed against the
two rendered authoritative page images before any PP-OCRv6 promotion decision.

## Next safe action
Keep sustained research disabled and `research-engine-daemon.service`
inactive/dead. Treat remote
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
   or the first hard error.

Do not start the daemon, invoke PaddleOCR-VL/Qwen/Codex, change production
routing, or materialize scientific state.

## Remaining work
- Execute PP-OCRv6 bounded inference measurement on Lambda.
- Review OCR output against the two rendered authoritative target pages.
- Decide PP-OCRv6 promotion separately for scan/textless and low-confidence
  text residuals.
- Then open PaddleOCR-VL-1.6 only on validated semantic visual regions /
  exhausted structural residuals.
- Qwen3.5-4B visual use remains conditional on PaddleOCR-VL failure/abstention.
- Qwen3.5-4B semantic EXTRACT/VERIFY remains bounded and contemporaneously
  controlled against STANDARD Codex.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative
capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced
research-engine evidence as the complete handoff. Do not rely on previous chat
state. Follow the capsule's exact `next_safe_action`.
