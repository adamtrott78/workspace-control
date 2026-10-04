<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## State
- Task: `research-engine-local-document-pipeline-v1`
- Stage: `residual_escalation_and_local_semantic_fallbacks`
- research-engine remote canonical: `d0debd205de46a608fce5b9a15f3fa0fdd6de4e6`
- research-engine Lambda/local last verified: `7a26e648ec409c96a3f9b7c8620f566658700894` clean
- research daemon: keep inactive/dead PID 0
- sustained research: disabled
- STANDARD Codex authoritative-PDF EXTRACT/VERIFY remains production semantic baseline

## Prior candidate outcomes
### PP-OCRv6
Resource/latency PASS but quality not promoted. The content-bearing chart improved
substantially over native text but retained visible OCR errors, and the original
image-only scan target proved nearly blank and must be replaced before scan
recovery can be adjudicated.

### PaddleOCR-VL-1.6
Three calls completed, but direct element-level inference was not promoted:
- model init: 1.4238369059967226 s
- Figure 6: 72.534 s first / 72.997 s repeat
- Figure 3: 108.519 s
- peak process VRAM: 19,956 MiB
- peak RSS: 2802.21 MiB

Figure 6 recovered useful model labels but fabricated unsupported numeric table
values and collapsed panel relations. Figure 3 recovered many visible labels
but did not preserve the shortcut topology. PaddleOCR-VL remains useful
perception/parser evidence, not semantic authority.

## Qwen3.5-4B targeted visual-semantic gate
research-engine PR #78 merged as
`d0debd205de46a608fce5b9a15f3fa0fdd6de4e6`.

- PR-head CI `37242434658`: PASS
- canonical-main CI `37242540771`: PASS
- contract:
  `benchmarks/document_intelligence/qwen35-visual-benchmark-contract.v1.json`
- runner:
  `deploy/run-qwen35-visual-benchmark.sh`

The gate uses the already-prefetched:
- model: `Qwen/Qwen3.5-4B`
- revision: `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- exact pinned two-shard safetensor checksums

Runtime:
- isolated vLLM 0.30.0
- one idle selected GPU
- bfloat16
- max model length 8192
- max sequences 1
- one image per prompt
- GPU memory utilization 0.65
- optimized default CUDA-graph serving path, not forced eager
- fail-fast CUDA allocation probe before model loading
- full vLLM process-tree RSS measurement plus selected-GPU memory delta

Qwen is run in non-thinking mode with a fixed seed and bounded output. The
benchmark performs exactly three calls:
1. Figure 6 first/cold
2. Figure 3 warm
3. Figure 6 warm repeat

The prompts test evidence rather than generic OCR:
- Figure 6 must recover the three panel/model relationships, dashed/bold line
  semantics, and plain-110 absence while keeping
  `curve_numeric_estimates=[]`; unprinted curve-value estimation is forbidden.
- Figure 3 must recover architecture columns, shortcut presence, solid/dotted
  shortcut relations, stage channel widths, and supplied caption FLOPs.

Structured JSON is required and fabricated-fact tolerance remains zero.

This local gate invokes no Codex. A successful local quality result must still
be human-reviewed and then compared against a separate contemporaneous
authoritative-PDF Codex visual control before promotion.

## Localization strategy
The working architecture is increasingly local-first:

```text
authoritative PDF
  -> deterministic native/structure
  -> specialized local formula/table/OCR/perception
  -> local multimodal/semantic model
  -> remote STANDARD Codex only on disagreement/low confidence/unsupported cases
  -> human review
```

If Qwen succeeds visually, the next high-leverage experiment is the same model
for bounded local semantic EXTRACT/VERIFY:
- EXTRACT: <=4 authoritative pages
- VERIFY: exact radius-0 cited page
- structured evidence with exact quote/page provenance
- zero fabricated/unlocatable evidence
- contemporaneous STANDARD Codex controls
- explicit remote-call avoidance and token-saving measurement

Production EXTRACT/VERIFY routing stays unchanged until those controls pass.

## Next safe action
Keep sustained research disabled and `research-engine-daemon.service`
inactive/dead.

Treat remote
`main@d0debd205de46a608fce5b9a15f3fa0fdd6de4e6`
as canonical and Lambda/local
`main@7a26e648ec409c96a3f9b7c8620f566658700894`
as the last verified clean state.

On Lambda:
1. require branch `main`, clean checkout, daemon inactive/dead PID 0;
2. fetch origin and require `origin/main` exactly
   `d0debd205de46a608fce5b9a15f3fa0fdd6de4e6`;
3. fast-forward only to that commit;
4. run `bash deploy/run-qwen35-visual-benchmark.sh`;
5. return the visible `OUTPUT_ROOT` plus
   `qwen35-visual-benchmark-report.json`, or the first hard error.

The runner must first prove that vLLM's bundled Torch can allocate CUDA on the
selected GPU. A failure there is runtime-binary compatibility only and must not
be scored as Qwen quality.

If all three Qwen calls complete, evaluate semantic quality separately from the
current resource ceilings. Exceptional quality may justify a later explicit
serving/resource-policy experiment, but this gate does not silently relax
thresholds.

Do not start the daemon, invoke Codex during this initial local gate, change
production routing, download alternate Qwen weights, or materialize scientific
state.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route.

Treat the authoritative capsule, synchronized Markdown handoff, exact durable
Git/runtime state, and referenced research-engine evidence as the complete
handoff.

Do not rely on previous conversation state. Follow the capsule's exact
`next_safe_action`.
