<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-document-pipeline-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-document-pipeline-v1
- Title: Research Engine Local Document Intelligence and Compute Offload v1
- Status: IN_PROGRESS
- Capsule schema: v2
- Current stage: residual_escalation_and_local_semantic_fallbacks

## Goal

Design, benchmark, and integrate a provenance-preserving local document-intelligence pipeline that converts content-addressed research PDFs into reusable LLM-ready paper packages, minimizes paid/plan semantic usage and repeated PDF interpretation, and systematically evaluates every research-engine stage for safe deterministic or local-model offload before production deployment on the Lambda.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint recorded by task: 134d60630a1bf16499fee169f28456a670de343f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 9d2e56513f134e4dbb83970402ff9feccccc9fb3
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD (last verified; not synchronized by GitHub-only contract work): 0e5b1464c5307b9b1824618b6e5cff0f13485146
- Local clean (last verified): true

## Durable residual-contract checkpoint

- `benchmarks/document_intelligence/residual-escalation-contract.v1.json` is merged and CI-locked.
- research-engine PR #64 merged as `9d2e56513f134e4dbb83970402ff9feccccc9fb3`.
- PR CI `37166055936`: PASS.
- canonical-main CI `37166127123`: PASS.
- Eight residual classes are explicit with openers, quality/provenance thresholds, fail-closed fall-through behavior, resource ceilings, token/allowance accounting, and contemporaneous authoritative-PDF Codex controls.
- Minimum new corpus expansion is exactly three source PDFs: `scan-mixed-quality-v1`, `semantic-visuals-v1`, and `malformed-layout-v1`.
- Formula/table residuals reuse the existing seven-paper corpus; semantic ambiguity reuses preserved authoritative source/calibration evidence.
- No new OCR/VLM/local-agent model/runtime was downloaded or enabled during this checkpoint.

## Next safe action

Keep sustained research disabled and do not start research-engine-daemon.service. Treat research-engine remote main@9d2e56513f134e4dbb83970402ff9feccccc9fb3 as the durable residual-contract baseline; the Lambda/local checkout remains last verified clean at 0e5b1464c5307b9b1824618b6e5cff0f13485146 because this checkpoint was GitHub-only. Do not fast-forward or install models merely to normalize that local checkout. First use the durable residual-escalation-contract.v1.json to select/pin the minimum concrete OCR/layout, multimodal-region, and local semantic candidate families with current license/runtime evidence, while separately preparing manifests for only scan-mixed-quality-v1, semantic-visuals-v1, and malformed-layout-v1. No global OCR/VLM/local-agent enablement, broad parser bakeoff, or sustained runtime work. Open Lambda model/runtime installation only after candidate selection plus source-case manifests are durable and a bounded benchmark gate explicitly owns local synchronization and daemon/model lifecycle.

## Remaining work

- Materialize/register only the three new source cases required by residual-escalation-contract.v1.json, keeping bulky PDFs outside Git and committing only manifests/annotations/hashes that belong in the benchmark repository.
- Now that the contract is durable, select and pin the smallest credible concrete candidate set: one local OCR/layout family, one document/region multimodal family, and one local text-reasoning family; document license/runtime constraints before any Lambda installation.
- Benchmark candidate local recovery tiers only on residuals whose oracle-free opener fires; preserve existing healthy born-digital/formula/table paths as non-regression controls rather than reopening the broad parser bakeoff.
- For any local semantic EXTRACT/VERIFY candidate, require contemporaneous STANDARD Codex controls over the same authoritative PDF pages/regions plus exact token/cached-token/reasoning-token and local resource telemetry.
- Promote only candidates that pass every quality/provenance/resource gate; low-confidence, timeout, disagreement, backpressure, or missing provenance must fall through to Codex and then human review.
- After measured promotion decisions, update localization-matrix.v2 or create the next measured version, CI-lock the production fallback ladder, and run a separate bounded Lambda integration gate before considering task completion or sustained research.

## Blockers / gates

- The three targeted missing corpus cases (scan-mixed-quality-v1, semantic-visuals-v1, malformed-layout-v1) have not yet been materialized/registered with authoritative PDF hashes and required annotations.
- Concrete OCR, multimodal-region, and local semantic candidate models/runtimes have not yet been selected, license-reviewed, pinned, or benchmarked against the now-durable residual contract.
- Codex STANDARD EXTRACT/VERIFY remains the semantic production baseline until a candidate passes its residual-specific contemporaneous authoritative-PDF control and resource/token gates.
- Sustained research remains disabled while residual fallback candidates are selected and benchmarked.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative task capsule, synchronized Markdown handoff, exact durable Git/runtime state, and referenced research-engine evidence as the complete handoff. Do not rely on previous conversation state. Follow the capsule's exact `next_safe_action`.
