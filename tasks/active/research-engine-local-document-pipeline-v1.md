<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: research-engine-local-document-pipeline-v1
- Stage: residual_escalation_and_local_semantic_fallbacks
- research-engine remote: `17aaa3182821fed8aacea2f710184b3c1f3ec2a3`
- Lambda/local last verified: `0e5b1464c5307b9b1824618b6e5cff0f13485146` clean
- daemon: last verified inactive/dead PID 0
- sustained research: disabled

## Durable stage artifacts
- residual escalation contract v1
- residual candidate selection v1
- source cases: `scan-mixed-quality-v1`, `semantic-visuals-v1`, `malformed-layout-v1`
- no candidate model/runtime has been downloaded or enabled

## Next safe action
Keep sustained research disabled and keep research-engine-daemon.service inactive/dead. Treat research-engine remote main@17aaa3182821fed8aacea2f710184b3c1f3ec2a3 as the durable source-registration baseline; Lambda/local remains last verified clean at 0e5b1464c5307b9b1824618b6e5cff0f13485146. Next implement and merge a deterministic bounded source-prefetch/audit gate only: download the three registered PDFs into visible workspace-control-tmp, capture authoritative SHA-256/page count, run existing Docling native and standard_no_ocr without new candidate weights, and evaluate the residual contract's scan/low-confidence/layout openers. The layout case must fail closed and be replaced if its opener does not fire. Do not install PP-OCRv6_medium, PaddleOCR-VL-1.6, Qwen3.5-4B, start the daemon, change production routing, or materialize scientific state until that source audit is durable and PASS.

## Remaining work
- Implement and CI-lock a bounded source-prefetch/audit harness that keeps the daemon stopped, downloads only the three registered PDFs to visible workspace-control-tmp, captures SHA-256/page counts, runs existing Docling native plus standard_no_ocr, and emits per-page deterministic residual-opener diagnostics.
- Run that gate on Lambda only after its code is merged; fail closed if any source URL/hash/download is invalid or if malformed-layout-v1 has no target page satisfying the layout opener.
- Use accepted scan/layout pages and located semantic-visual regions to finalize compact human annotations/region locators without committing bulky PDFs or rendered crops.
- Only after source audit acceptance open a separate bounded model-prefetch gate for PP-OCRv6_medium, PaddleOCR-VL-1.6, and Qwen3.5-4B with exact license/checksum/resource receipts.
- Then benchmark residual-scoped candidates with contemporaneous authoritative-PDF Codex controls where required; update localization matrix only after measured promotions.

## Gates
- The authoritative binaries for the three registered source cases have not yet been downloaded on Lambda, SHA-256 pinned, or audited with production-equivalent native/structure openers.
- malformed-layout-v1 remains a source candidate until its deterministic layout opener fires; it must be replaced if it fails that audit.
- Selected OCR/VLM/local-semantic candidate runtimes and weights remain uninstalled and unmeasured; their prefetch gate is still closed until the source audit passes.
- Codex STANDARD EXTRACT/VERIFY remains the semantic production baseline and sustained research remains disabled.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced research-engine evidence as the complete handoff. Do not rely on previous chat state. Follow the capsule's exact `next_safe_action`.
