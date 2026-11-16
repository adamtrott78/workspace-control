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
- Remote checkpoint: 9b02005a58a961ce83ef8790e2d59ec626802591
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

SCREENING IS COMPLETE AND THE CLAIM-BEARING PLAN IS FROZEN. Validated screening-completion head 91dcc8520cc7e348c1f6bf2e16044b096d89c5bf passed Workspace #2890 / Semantic #219 / Operator #498; validated scored-plan head 9b02005a58a961ce83ef8790e2d59ec626802591 passed Workspace #2891 / Semantic #220 / Operator #499. The plan binds 18 required arm×phenotype cells × 3 replicates = 54 claim-bearing runs, but authorizes zero launches. DO NOT materialize or manually grind through those runs while live Instant/operator transport is authority-gated or allowance calibration is UNKNOWN. Codex remains suspended on PR #627/#630. When an authorized live executor and calibrated comparable weekly meter exist, admit/materialize scored runs through the existing governor/runset gate and preserve matched_work_item_id sets for holdout promotion.

## Remaining work

- Execute the frozen 54-run claim-bearing scored-replicate plan only after live executor authority and a calibrated comparable allowance relationship exist; materialize run-state files lazily at admission time, not in advance.
- Preserve UNKNOWN allowance for traces without controlled comparable meter deltas; never infer shared allowance from raw tokens.
- When PR #627/#630 lineage clears, run reserved Workspace Control zero-inference Codex bootstrap and prove account.type=chatgpt, planType=plus, OPENAI_API_KEY absent, no API billing/fallback.
- Run isolated controlled Codex and Instant actions bracketed by official account/rate-limit/usage snapshots; determine which meter actually moves and keep unresolved mappings unknown.
- Feed calibrated traces into weekly governor + matched holdout protocol and compare validated progress per scarce allowance against all-strong/frontier control.
- Promote a routing policy only with claim-bearing comparable evidence, quality-floor PASS and strictly lower scarce allowance.

## Blockers / gates

- LIVE CODEX LINEAGE AUTHORITY: PR #627 and stacked PR #630 remain open drafts at their validated SHAs. Live Codex runtime/auth is suspended until the reserved-capacity lineage reaches a trusted/default-branch promotion path; API billing and manual runner/sidecar bypass remain forbidden.
- CLAIM-BEARING EXECUTION GATE: protocol screening is complete and the exact 54-run scored-replicate plan is frozen, but launch remains blocked because live Instant/operator transport lacks reviewed Workspace Shell authority and the shared ChatGPT/Codex weekly allowance relationship is still UNKNOWN. Do not spend 54 manual clean-chat runs or treat unknown meter cost as free.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-reasoning-economy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
