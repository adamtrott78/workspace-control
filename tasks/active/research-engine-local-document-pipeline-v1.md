<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: research-engine-local-document-pipeline-v1
- Stage: residual_escalation_and_local_semantic_fallbacks
- research-engine remote canonical: `93d1f2c9c8fe120084512cf4fa44e1e6606a9a9a`
- research-engine Lambda/local last verified: `0e5b1464c5307b9b1824618b6e5cff0f13485146` clean
- research daemon: last verified inactive/dead PID 0
- sustained research: disabled

## Durable residual work
- residual escalation contract v1: merged/CI-locked
- benchmark candidate selection v1: merged/CI-locked
- three residual source manifests: merged/CI-locked
- bounded deterministic source audit: merged/CI-locked and READY_FOR_LAMBDA
- source audit runner: `deploy/run-residual-source-prefetch-audit.sh`
- candidate model downloads/inference remain zero

## Source-audit representation correction
The current Docling normalizer retains pictures as FIGURE document blocks with
caption linkage in derivation metadata; it does not currently materialize
FigureAsset records. The audit implementation was corrected to consume that
production representation and a real normalizer regression test now locks it.

## Next safe action
Keep sustained research disabled and research-engine-daemon.service inactive/dead. Treat research-engine remote main@93d1f2c9c8fe120084512cf4fa44e1e6606a9a9a as the canonical bounded-source-audit baseline and Lambda/local main@0e5b1464c5307b9b1824618b6e5cff0f13485146 as the last verified local state. On Lambda, first require branch=main, clean checkout, and daemon inactive/dead PID 0; fetch origin and require origin/main exactly 93d1f2c9c8fe120084512cf4fa44e1e6606a9a9a, then fast-forward only to that commit. Run bash deploy/run-residual-source-prefetch-audit.sh. Return the visible OUTPUT_ROOT plus residual-source-audit-report.json, or the first hard error/rejection. Do not install or invoke PP-OCRv6_medium, PaddleOCR-VL-1.6, Qwen3.5-4B, start the daemon, invoke Codex, change production routing, or materialize scientific state. A REJECT means revise only the failed source/region and rerun this deterministic gate; PASS requires model_prefetch_ready=true before the separate model-prefetch stage opens.

## Remaining work
- On Lambda with research-engine-daemon.service inactive/dead, require clean main@0e5b1464c5307b9b1824618b6e5cff0f13485146, fetch origin/main, require origin/main=93d1f2c9c8fe120084512cf4fa44e1e6606a9a9a, and fast-forward only to that canonical commit.
- Run bash deploy/run-residual-source-prefetch-audit.sh. Preserve the visible output root and return the compact audit report or first hard failure.
- If the audit REJECTS malformed-layout-v1, replace only that source manifest and rerun the source gate; do not relax opener thresholds or install a layout/VLM model.
- If semantic visual targets do not both resolve to unique caption-linked bboxes, refine/replace only the source-region selection before any VLM prefetch.
- If the audit PASSES with model_prefetch_ready=true, durably pin downloaded PDF SHA-256/page counts and accepted opener/region evidence, then implement a separate bounded model-prefetch/license/checksum gate for the already-selected candidates.
- Only after model prefetch/audit should residual-scoped quality/resource benchmarks and contemporaneous Codex controls begin.

## Gates
- Lambda/local research-engine is still last verified clean at main@0e5b1464c5307b9b1824618b6e5cff0f13485146 while canonical remote main is 93d1f2c9c8fe120084512cf4fa44e1e6606a9a9a; synchronize only as part of the bounded source-audit run while the daemon is stopped.
- The bounded source-prefetch/audit has not yet executed on Lambda, so authoritative SHA-256/page counts, actual scan/text opener pages, semantic figure bboxes, and malformed-layout acceptance/replacement are still unresolved.
- Selected candidate OCR/VLM/local-semantic runtimes and weights remain intentionally uninstalled until the source audit returns PASS with model_prefetch_ready=true.
- Codex STANDARD EXTRACT/VERIFY remains the semantic production baseline; sustained research remains disabled.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced research-engine evidence as the complete handoff. Do not rely on previous chat state. Follow the capsule's exact `next_safe_action`.
