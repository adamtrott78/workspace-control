<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: `research-engine-local-document-pipeline-v1`
- Stage: `residual_escalation_and_local_semantic_fallbacks`
- research-engine remote canonical: `320bfd037ce51dee63dc1ec4bb0e7d5d984d2c5c`
- research-engine Lambda/local last verified: `d9946729f92a15fe3a6c821dc366a53a37ca0756` clean
- research daemon: keep inactive/dead PID 0
- sustained research: disabled
- Codex STANDARD authoritative-PDF EXTRACT/VERIFY remains production semantic baseline

## Corrected residual source gate
The corrected bounded Lambda source audit is PASS with
`model_prefetch_ready=true`.

Safety counters:
- candidate model downloads: 0
- candidate model inference calls: 0
- scientific state materialized: false
- authority: downloaded original PDFs

Pinned source evidence:
- `scan-mixed-quality-v1`: SHA-256
  `3948255a723380d8844bab31c60298cee00da9334efa377f1d596b306792b6a1`,
  28 pages; scan opener pages zero-based `[1,3,5,27]`; low-confidence pages
  `[8,9,15,16,19,22,24]`.
- `semantic-visuals-v1`: SHA-256
  `1e0651b6810ecba34a3dbc5b5b0209226f889004607c1f203540a48d64e5a93a`,
  12 pages; Figure 6 page index 7 bbox
  `[99.19828033447266,72.1703872680664,495.0450134277344,171.62620544433594]`;
  Figure 3 page index 3 bbox
  `[50.5037956237793,76.09317016601562,285.709716796875,618.7928466796875]`.
- `malformed-layout-v1`: SHA-256
  `f2630182ccfabd6fc89ac20270b4daf15a0ca849298a7db1e5d124ca443051f1`,
  14 pages; both registered targets fire the layout opener and no replacement is required.

The compact uploaded audit report SHA-256 is
`ade43b862493a6b21f3684a75870861769dcf7831c7fa6dbda7026df5081eb1c`.

## Model prefetch gate
research-engine PR #70 merged as
`320bfd037ce51dee63dc1ec4bb0e7d5d984d2c5c`.

- PR-head CI `37171098792`: PASS
- canonical-main CI `37171236633`: PASS
- source PASS receipt: `benchmarks/document_intelligence/residual-source-audit-pass.v1.json`
- contract: `benchmarks/document_intelligence/residual-model-prefetch-contract.v1.json`
- runner: `deploy/run-residual-model-prefetch-gate.sh`

The gate prefetches four artifact repositories across the three selected
candidate families:
1. PP-OCRv6 medium detection
2. PP-OCRv6 medium recognition
3. PaddleOCR-VL-1.6
4. Qwen3.5-4B

It records exact resolved revisions, Apache-2.0 license metadata, per-file
SHA-256 manifests, materialized bytes, offline reopenability, disk/host/GPU
compatibility facts, and the pinned PaddleOCR 3.7.0 wheel.

It performs zero candidate inference and does not install PaddlePaddle, vLLM,
SGLang, Transformers, or another candidate inference runtime.

## Next safe action
Keep sustained research disabled and `research-engine-daemon.service`
inactive/dead. Treat research-engine remote
`main@320bfd037ce51dee63dc1ec4bb0e7d5d984d2c5c` as canonical and Lambda/local
`main@d9946729f92a15fe3a6c821dc366a53a37ca0756` as the last verified local
state.

On Lambda:
1. require branch `main`, clean checkout, daemon inactive/dead PID 0;
2. fetch origin and require `origin/main` exactly
   `320bfd037ce51dee63dc1ec4bb0e7d5d984d2c5c`;
3. fast-forward only to that commit;
4. run `bash deploy/run-residual-model-prefetch-gate.sh`;
5. return the visible `OUTPUT_ROOT` plus `model-prefetch-report.json`, or the
   first hard failure.

Do not start the daemon, run candidate OCR/VLM/semantic inference, install
PaddlePaddle/vLLM/SGLang/Transformers, invoke Codex, change production routing,
or materialize scientific state.

A PASS opens isolated PP-OCRv6 runtime construction and the first scan/text
quality/resource benchmark. PaddleOCR-VL follows on targeted visual/structural
residuals; Qwen3.5-4B semantic benchmarking remains bounded and contemporaneously
controlled against STANDARD Codex.

## Remaining work
- Execute the bounded model artifact prefetch gate on Lambda.
- Pin the resolved PP-OCRv6 detection/recognition revisions and compact
  prefetch/license/checksum receipts.
- Build isolated PP-OCRv6 inference runtime and human-check the promoted
  scan/text benchmark targets.
- Run PP-OCRv6 quality/resource benchmark first.
- Then open PaddleOCR-VL-1.6 only on validated target regions / exhausted
  structural residuals.
- Open Qwen3.5-4B semantic EXTRACT/VERIFY only on bounded authoritative-PDF
  inputs with contemporaneous STANDARD Codex controls.
- Qwen visual use remains conditional on PaddleOCR-VL failure/abstention.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative
capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced
research-engine evidence as the complete handoff. Do not rely on previous chat
state. Follow the capsule's exact `next_safe_action`.
