<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: research-engine-local-document-pipeline-v1
- Stage: residual_escalation_and_local_semantic_fallbacks
- research-engine remote canonical: `d9946729f92a15fe3a6c821dc366a53a37ca0756`
- research-engine Lambda/local last verified: `4d77fb64c5befb55362e9f689ef5b3c85d2c1f35` clean
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

## Completed source-audit evidence
- `scan-mixed-quality-v1`: accepted; scan pages `[1,3,5,27]`; low-confidence pages `[8,9,15,16,19,22,24]`.
- `malformed-layout-v1`: accepted; both registered target pages fired the layout opener.
- `semantic-visuals-v1`: both targets resolved to one `LINKED_FIGURE` bbox each.
- The completed report emitted `REJECT` only because stale acceptance code separately required standalone caption blocks.
- candidate model downloads/inference remained zero; scientific state remained untouched.

## Semantic-linkage hotfix
- research-engine PR #69 -> `d9946729f92a15fe3a6c821dc366a53a37ca0756`
- PR CI `37170199764`: PASS
- canonical-main CI `37170287404`: PASS
- semantic acceptance now follows normalized FIGURE caption linkage + bbox and does not require a separately materialized caption block.

## Next safe action
Keep sustained research disabled and research-engine-daemon.service inactive/dead. Fast-forward Lambda from clean main@4d77fb64c5befb55362e9f689ef5b3c85d2c1f35 to canonical main@d9946729f92a15fe3a6c821dc366a53a37ca0756. Reuse the newest completed residual-source-prefetch-audit output root and replay only `research_engine.residual_source_audit audit` against its preserved `sources/` and `packages/`. Do not rerun Docling unless artifact validation fails. Require `decision=PASS`, `model_prefetch_ready=true`, all three cases accepted, zero candidate downloads/inference, and `scientific_state_materialized=false`.

## Remaining work
- Replay corrected deterministic source audit only.
- On PASS, durably pin hashes/page counts and accepted opener/region evidence.
- Then open the separate bounded model-prefetch/license/checksum/resource gate for the already-selected candidates.
- Only after that begin residual-scoped OCR/VLM/local-semantic benchmarks with contemporaneous authoritative-PDF Codex controls.

## Gates
- Lambda/local is one semantic-linkage hotfix commit behind canonical research-engine main.
- The underlying source evidence is good; only the corrected report replay remains.
- Candidate OCR/VLM/local-semantic runtimes and weights remain intentionally uninstalled.
- Codex STANDARD EXTRACT/VERIFY remains the semantic production baseline.
- Sustained research remains disabled.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced research-engine evidence as the complete handoff. Do not rely on previous chat state. Follow the capsule's exact `next_safe_action`.
