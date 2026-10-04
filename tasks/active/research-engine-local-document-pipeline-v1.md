<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: research-engine-local-document-pipeline-v1
- Stage: residual_escalation_and_local_semantic_fallbacks
- research-engine remote checkpoint: `9c636c4f00e47a8b8e507e4e011d4867a5da68f9`
- research-engine Lambda/local last verified checkpoint: `0e5b1464c5307b9b1824618b6e5cff0f13485146` (clean; not synchronized by GitHub-only work)
- sustained research: disabled
- daemon: last verified inactive/dead PID 0

## Durable residual architecture
- Contract: `benchmarks/document_intelligence/residual-escalation-contract.v1.json`
- Candidates: `benchmarks/document_intelligence/residual-candidate-selection.v1.json`
- Selected only for benchmarking: `PP-OCRv6_medium` -> `PaddleOCR-VL-1.6@c5630abae1d940eafe0697512a0325494b02ab42` -> `Qwen3.5-4B@851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- No model/runtime download or production enablement has occurred.
- Existing CodeFormulaV2 and FAST -> ACCURATE -> PP-TableMagic paths remain unchanged.

## Next safe action
Keep sustained research disabled and do not start research-engine-daemon.service. Treat research-engine remote main@9c636c4f00e47a8b8e507e4e011d4867a5da68f9 as the durable candidate-selection baseline; Lambda/local remains last verified clean at 0e5b1464c5307b9b1824618b6e5cff0f13485146 and should not be synchronized merely for bookkeeping. Next durably register exactly the three missing source-case manifests without moving bulky PDFs through GitHub: scan-mixed-quality-v1, semantic-visuals-v1, malformed-layout-v1. Each manifest must record a stable public/source locator, intended target pages/regions and annotations, and explicitly defer authoritative SHA-256 plus native opener diagnostics to the bounded Lambda prefetch/audit gate. Only after all three manifests are merged/CI-locked may a bounded Lambda gate own the fast-forward, source download/hash audit, selected model/runtime prefetch, license/checksum receipts, and candidate benchmarks. No global OCR/VLM/local-agent enablement and no broad parser bakeoff.

## Remaining work
- Durably register exactly three missing source cases: one degraded scanned scientific report, one scientific PDF with quantitative chart plus relational diagram semantics, and one complex born-digital/hybrid layout case whose acceptance remains contingent on the deterministic layout opener firing during native audit.
- Keep source PDF bytes outside Git where practical; record stable URLs/identifiers and target page/region annotations now, then capture authoritative SHA-256/page-count/native text-layout diagnostics during a bounded Lambda source-prefetch gate.
- After all three case manifests are durable, create one bounded Lambda gate that fast-forwards from the last verified local baseline, downloads only the selected/pinned candidate runtimes/weights into explicit caches, records exact licenses/checksums/resource preflight, and leaves research-engine-daemon.service inactive/dead.
- Benchmark PP-OCRv6_medium first only on scan/text residuals, PaddleOCR-VL-1.6 only on opened visual/exhausted specialized regions, and Qwen3.5-4B only on bounded semantic ambiguity plus conditional visual fallback.
- Require contemporaneous authoritative-PDF STANDARD Codex controls for any semantic/visual promotion, exact token telemetry, and fail-closed fall-through on timeout/backpressure/disagreement/missing provenance.
- After measured promotion decisions, update the localization matrix and CI-lock any production fallback ladder before a separate bounded integration gate.

## Gates
- The three targeted missing corpus cases (scan-mixed-quality-v1, semantic-visuals-v1, malformed-layout-v1) are not yet durably registered with stable source locations, target pages/regions, and later Lambda hash/native-opener audit requirements.
- Selected candidate runtimes have not yet been installed/prefetched or measured on the Lambda; exact PP-OCRv6 weight metadata/checksum and runtime dependency receipts remain gated behind source-case durability.
- Codex STANDARD EXTRACT/VERIFY remains the semantic production baseline until a candidate passes its residual-specific contemporaneous authoritative-PDF control and resource/token gates.
- Sustained research remains disabled while source cases and bounded candidate benchmarks are prepared.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced research-engine evidence as the complete handoff. Do not rely on previous chat state. Follow the capsule's exact `next_safe_action`.
