<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: research-engine-local-document-pipeline-v1
- Stage: residual_escalation_and_local_semantic_fallbacks
- research-engine remote canonical: `4d77fb64c5befb55362e9f689ef5b3c85d2c1f35`
- research-engine Lambda/local last verified: `93d1f2c9c8fe120084512cf4fa44e1e6606a9a9a` clean
- research daemon: keep inactive/dead PID 0
- sustained research: disabled

## Durable residual work
- residual escalation contract v1: merged/CI-locked
- benchmark candidate selection v1: merged/CI-locked
- three residual source manifests: merged/CI-locked
- bounded deterministic source audit: merged/CI-locked
- GPU-selector capture hotfix: PR #68 -> `4d77fb64c5befb55362e9f689ef5b3c85d2c1f35`
- PR-head CI `37169271564`: PASS
- canonical-main CI `37169339826`: PASS
- candidate model downloads/inference remain zero

## First Lambda source-audit attempt
The first bounded invocation reached source prefetch and the first document conversion but
did not reach deterministic opener evaluation. `select_structure_gpu` emitted probe
diagnostics and JSON on stdout; command substitution therefore captured a multi-line value
instead of GPU index `0`, making `CUDA_VISIBLE_DEVICES` invalid for the
`standard_no_ocr` Docling runtime.

The native conversion of `scan-mixed-quality-v1` completed. The standard conversion failed
with `docling.exceptions.AcceleratorDeviceNotAvailableError`. No
`residual-source-audit-report.json` was emitted, so source acceptance and
`model_prefetch_ready` remain unresolved.

Source fetch/hash/page-count validation did pass:
- `scan-mixed-quality-v1`: 28 pages, SHA-256 `3948255a723380d8844bab31c60298cee00da9334efa377f1d596b306792b6a1`
- `semantic-visuals-v1`: 12 pages, SHA-256 `1e0651b6810ecba34a3dbc5b5b0209226f889004607c1f203540a48d64e5a93a`
- `malformed-layout-v1`: 14 pages, SHA-256 `f2630182ccfabd6fc89ac20270b4daf15a0ca849298a7db1e5d124ca443051f1`

The failed diagnostic output root is:
`/home/atrott/adamArchives/Adam/workspace-control-tmp/residual-source-prefetch-audit-20261004T013615Z`

## Hotfix
The runner now routes GPU probe diagnostics/JSON to stderr so stdout contains only the
selected index, and it fails closed unless the captured `structure_gpu` value is numeric.
No benchmark threshold, source manifest, candidate selection, production routing, daemon
policy, or scientific-state behavior changed.

## Next safe action
Keep sustained research disabled and research-engine-daemon.service inactive/dead. Treat research-engine remote main@4d77fb64c5befb55362e9f689ef5b3c85d2c1f35 as the canonical bounded-source-audit hotfix baseline and Lambda/local main@93d1f2c9c8fe120084512cf4fa44e1e6606a9a9a as the last verified local state. On Lambda, require branch=main, clean checkout, and daemon inactive/dead PID 0; fetch origin and require origin/main exactly 4d77fb64c5befb55362e9f689ef5b3c85d2c1f35, then fast-forward only to that commit. Rerun bash deploy/run-residual-source-prefetch-audit.sh. Return the new visible OUTPUT_ROOT plus residual-source-audit-report.json, or the first hard error/rejection. Do not install or invoke PP-OCRv6_medium, PaddleOCR-VL-1.6, Qwen3.5-4B, start the daemon, invoke Codex, change production routing, or materialize scientific state. A REJECT means revise only the failed source/region and rerun this deterministic gate; PASS requires model_prefetch_ready=true before the separate model-prefetch stage opens.

## Remaining work
- On Lambda with research-engine-daemon.service inactive/dead, require clean main@93d1f2c9c8fe120084512cf4fa44e1e6606a9a9a, fetch origin/main, require origin/main=4d77fb64c5befb55362e9f689ef5b3c85d2c1f35, and fast-forward only to that canonical hotfix commit.
- Rerun `bash deploy/run-residual-source-prefetch-audit.sh`. Preserve the new visible output root and return the audit report or first hard failure.
- If the audit REJECTS `malformed-layout-v1`, replace only that source manifest and rerun; do not relax thresholds or install a model.
- If semantic visual targets do not resolve to unique caption-linked bboxes, refine/replace only those source regions before VLM prefetch.
- If the audit PASSES with `model_prefetch_ready=true`, durably pin source hashes/page counts and accepted opener/region evidence, then implement the separate bounded model-prefetch/license/checksum gate.
- Only after model prefetch/audit should residual-scoped OCR/VLM/local-semantic quality/resource benchmarks and contemporaneous Codex controls begin.

## Gates
- Lambda/local is one hotfix commit behind canonical research-engine main.
- The source PDFs are fetched and hashed, but deterministic residual opener/region acceptance has not completed.
- Selected PP-OCRv6_medium, PaddleOCR-VL-1.6, and Qwen3.5-4B runtimes/weights remain intentionally uninstalled.
- Codex STANDARD EXTRACT/VERIFY remains the semantic production baseline.
- Sustained research remains disabled.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced research-engine evidence as the complete handoff. Do not rely on previous chat state. Follow the capsule's exact `next_safe_action`.
