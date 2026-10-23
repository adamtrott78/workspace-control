<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-plugin-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-plugin-v1
- Title: Workspace Heartbeat MCP Plugin v1
- Status: COMPLETE
- Capsule schema: v2

## Goal

Preserve the accepted Workspace Heartbeat v0.4.5 lifecycle and semantic behavior while correcting live-card iframe sizing so short turns do not leave large blank transcript gaps.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-heartbeat-v046-current-main-restage
- Remote checkpoint: 050198002dfcf01c2520871d08b858bf43072547
- Remote verified: true

## Next safe action

v0.4.6 accepted: PR #280 merged at cd396157d7e3e5c3f955c15e41bebba501057693. Preserve v0.4.5 rollback; continue separate v0.4.7 liveness task.

## Remaining work

- Validate one planned chat-to-chat handoff: outgoing chat synchronizes durable handoff state, sends terminal Heartbeat done, and a fresh receiving chat begins the same task_id without a server restart.
- After that handoff PASS, mark the v0.4.6 stage VALIDATED/task COMPLETE and merge the fresh current-main restage branch rather than stale PR #155.
- Preserve the accepted v0.4.5 rollback and stop; executor-liveness implementation is owned by workspace-heartbeat-executor-liveness-v1.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-plugin-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.

## 2026-10-23 receiving-chat checkpoint

Planned cross-chat handoff PASS using the same task ID without server restart. v0.4.6 was merged through fresh restage PR #280 at `cd396157d7e3e5c3f955c15e41bebba501057693`. Observation-only liveness work is separately staged as v0.4.7; automatic takeover remains disabled.
