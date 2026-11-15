<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-reasoning-economy-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-reasoning-economy-v1
- Title: Workspace Reasoning Economy v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Build and empirically tune a subscription-aware reasoning economy layer for Workspace Semantic Execution. Programmatically observe Codex/ChatGPT-backed account usage and rate-limit state through the authenticated Codex app-server; record per-task execution economics; route/decompose work toward the least-scarce capable executor; and use Research Engine as the first CPU-only learning workload while preserving verified quality.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-semantic-execution-migration-v1
- Remote checkpoint: 65709645abfb14b88a51f01296bc3b9600aca919
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement RESEARCH_ENGINE_POLICY_EXPERIMENT_TRACE_ADAPTER_V1 without invoking a live model. Bind the existing provenance-refrozen P0-P3 resumable-reasoning matrix, fixture/oracle blob identities, arm/run identities and objective validator outputs into typed policy experiment records. Join those records to ExecutionEconomics only when exact work/run identity and a comparable weekly allowance delta are available; otherwise mark allowance UNKNOWN. Produce matched-policy summaries and holdout-ready rows, but do not promote a policy or infer shared ChatGPT/Codex accounting until live calibration exists. Keep Codex live runtime suspended on PR #627/#630 lineage.

## Remaining work

- Build the frozen P0-P3 Research Engine/research-iterate policy-trace adapter using exact fixture/oracle provenance and objective validator results.
- Produce policy experiment reports that preserve UNKNOWN allowance when a run lacks a comparable calibrated weekly meter delta; do not synthesize costs from token counts.
- When PR #627/#630 lineage clears, run the reserved Workspace Control zero-inference Codex bootstrap/auth preflight and prove ChatGPT Plus account telemetry.
- Calibrate controlled Codex/Instant actions against account/rate-limit snapshots to determine which meter tracks the shared allowance; preserve unknown mappings explicitly.
- Feed calibrated real traces into the weekly governor and matched holdout promotion protocol.
- Compare verified progress per scarce allowance against an all-strong/frontier control policy and promote only if quality floors and holdout criteria pass.

## Blockers / gates

- LIVE CODEX LINEAGE AUTHORITY: PR #627 and stacked PR #630 remain open drafts at their validated SHAs. Live Codex runtime/auth is suspended until the reserved-capacity lineage reaches a trusted/default-branch promotion path; API billing and manual runner/sidecar bypass remain forbidden.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-reasoning-economy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
