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
- Remote checkpoint: 74958b5d0d325893fd39045d1e49b5320dca7fa3
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

DEFAULT-BRANCH CODEX LINEAGE IS PROMOTED; CLAIM-BEARING 54-RUN EXECUTION REMAINS FAIL-CLOSED. Next run the zero-inference control-small Codex bootstrap from main@5cf2821c2aac415cba72ff3798f89afa01052cbf and verify its receipt/auth runtime. After that, run only the minimum controlled Codex/Instant allowance calibration needed to establish comparable telemetry. Do not launch/materialize the frozen 54 scored runs until live evaluator isolation, calibrated allowance, and reviewed live executor authority are all satisfied.

## Remaining work

- Execute the frozen 54-run claim-bearing scored-replicate plan only after live executor authority, live evaluator-isolation acceptance, and a calibrated comparable allowance relationship all exist; materialize run-state files lazily at admission time.
- Preserve UNKNOWN allowance for traces without controlled comparable meter deltas; never infer shared allowance from raw tokens.
- Run the default-main zero-inference Workspace Control Codex bootstrap and verify the control-small receipt; prove account.type=chatgpt, planType=plus, OPENAI_API_KEY absent, and no API billing/fallback before any live inference.
- Run isolated controlled Codex and Instant actions bracketed by official account/rate-limit/usage snapshots; determine which meter actually moves and keep unresolved mappings unknown.
- Feed calibrated traces into weekly governor + matched holdout protocol and compare validated progress per scarce allowance against all-strong/frontier control.
- Promote a routing policy only with claim-bearing comparable evidence, quality-floor PASS and strictly lower scarce allowance.

## Blockers / gates

- LIVE CODEX BOOTSTRAP: #627/#630 reserved-capacity + inert Codex bootstrap lineage is now promoted to default main@5cf2821c2aac415cba72ff3798f89afa01052cbf. The remaining runtime gate is a zero-inference bootstrap receipt proving the control-small route/auth environment. API billing and manual runner/sidecar bypass remain forbidden.
- CLAIM-BEARING EXECUTION GATE: protocol screening is complete and the exact 54-run scored plan is frozen, but launch remains blocked on three independent gates: reviewed live Instant/operator authority, live evaluator sealed-store worker-denial/readback acceptance, and calibrated shared ChatGPT/Codex weekly allowance telemetry. Do not spend 54 manual clean-chat runs or treat UNKNOWN meter cost as free.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-reasoning-economy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
