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
- Remote checkpoint: fc5bdb47f2ba31c1c64c06eca4c1612397d2ce26
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

## Next safe action

Implement a Codex subscription auth inspector using read-only account/read, fail closed unless account.type=chatgpt, and a codex exec --json trace parser that captures thread id, turn success/failure, input/cached/output/reasoning-output tokens, command/MCP/web/collab/file-change counts, and errors. Then implement a subscription-only executor wrapper that strips OPENAI_API_KEY, refuses unknown/API-key auth, snapshots account usage before/after, and returns structured execution economics. Unit-test all behavior with fixture processes before any live login/invocation.

## Remaining work

- Implement subscription-only Codex executor with ChatGPT-auth guard and JSONL trace ingestion.
- Calibrate account/usage/read and rate-limit deltas against controlled ChatGPT/Codex/Instant actions.
- Run Research Engine routing/decomposition experiments.
- Implement weekly burn governor and recursive policy promotion.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-reasoning-economy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
