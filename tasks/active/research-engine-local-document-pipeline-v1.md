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

## Goal

Design, benchmark, and integrate a provenance-preserving local document-intelligence pipeline that converts content-addressed research PDFs into reusable LLM-ready paper packages, minimizes paid/plan semantic usage and repeated PDF interpretation, and systematically evaluates every research-engine stage for safe deterministic or local-model offload before production deployment on the Lambda.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 134d60630a1bf16499fee169f28456a670de343f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 1d461988a9416937a9149e4dd8faeeb666ac0e03
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 1d461988a9416937a9149e4dd8faeeb666ac0e03
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. Treat research-engine main@1d461988a9416937a9149e4dd8faeeb666ac0e03 as the validated shared-inference/concurrency baseline. Begin extract_verify_paper_package_ab by inspecting the current EXTRACT/VERIFY hydrator and existing replay/telemetry contracts, then design and CI-gate a non-materializing A/B harness that compares the current authoritative-PDF context path against paper-package-derived context on preserved verified sources. Preserve original-PDF authority and source locators, measure evidence/provenance agreement plus exact semantic token/latency/local-compute telemetry, do not mutate scientific state, and keep plan-allowance observations separate from token counts. Do not reopen parser/model bakeoffs.

## Remaining work

- Design and CI-gate a non-materializing EXTRACT/VERIFY A/B harness over the preserved research corpus comparing the current authoritative-PDF hydration path with paper-package-derived context.
- Measure evidence/provenance agreement, semantic input/cached/output/reasoning tokens, latency, and local-compute cost separately; retain exact token telemetry and treat plan-allowance UI observations as censored/quantized evidence only.
- Keep fail-closed access to authoritative PDF pages/regions and do not mutate scientific state during A/B replay.
- Run the bounded stopped-daemon Lambda A/B gate and decide whether paper-package context is quality-safe enough to replace repeated PDF interpretation for EXTRACT/VERIFY.
- Then finish the broader research_pipeline_localization_matrix_validation and Lambda production acceptance.

## Blockers / gates

- CodeFormulaV2 deployment/redistribution obligations still require final license/deployment review before sustained production enablement.
- EXTRACT/VERIFY paper-package A/B has not yet demonstrated evidence/provenance equivalence and semantic-token/allowance savings versus the current authoritative-PDF path; production replacement remains forbidden until measured.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
