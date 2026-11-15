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
- Remote checkpoint: 41d320100a0c2ee3890c900ed5295a94b08213af
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

CONTINUE FROM validated Reasoning Economy base workspace-control@41d320100a0c2ee3890c900ed5295a94b08213af. Do not rebuild the weekly governor (65709645…), frozen Research Engine policy-trace adapter (fadadcc0…), shared-allowance calibration harness (59d69e0f…), claim-bearing runset readiness gate (31f138a8…), or dispatch-time allowance admission (41d32010…). Continue only exact claim-bearing P0-P3 screening/runset readiness and holdout preparation; superseded/refrozen-but-incomplete runs are NOT promotion evidence and allowance remains UNKNOWN without comparable calibrated meter deltas. Codex live runtime stays SUSPENDED until PR #627/#630 lineage authority clears. When it clears, run zero-inference bootstrap/auth, then controlled isolated Codex/Instant snapshots and feed only calibrated observations into the governor/holdout promotion protocol.

## Remaining work

- Complete claim-bearing P0-P3 screening/runset prerequisites with exact source checkpoint/run set/hard-gate manifest; incomplete or superseded screening cannot promote policy.
- Preserve UNKNOWN allowance for traces without controlled comparable meter deltas; never infer shared allowance from raw tokens.
- When PR #627/#630 lineage clears, run reserved Workspace Control zero-inference Codex bootstrap and prove account.type=chatgpt, planType=plus, OPENAI_API_KEY absent, no API billing/fallback.
- Run isolated controlled Codex and Instant actions bracketed by official account/rate-limit/usage snapshots; determine which meter actually moves and keep unresolved mappings unknown.
- Feed calibrated traces into weekly governor + matched holdout protocol and compare validated progress per scarce allowance against all-strong/frontier control.
- Promote a routing policy only with claim-bearing comparable evidence, quality-floor PASS and strictly lower scarce allowance.

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
