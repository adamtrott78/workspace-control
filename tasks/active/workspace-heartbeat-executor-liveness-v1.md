<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-executor-liveness-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-executor-liveness-v1
- Title: Workspace Heartbeat Executor Liveness v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Give the operator, inside the existing Heartbeat card and without opening a new chat, an independent view of demonstrated assistant-executor liveness that remains useful when the ChatGPT website says connection interrupted. Keep semantic progress and executor activity separate, then use the same observation layer later for bounded stale-owner recovery.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-heartbeat-executor-liveness-v1
- Remote checkpoint: ac4d321f056d5b9a30f6dce2f78dfb7617affb06
- Remote verified: true

## Next safe action

Validate the isolated observation-only v0.4.7 candidate with CI; no live deployment or automatic stale-owner takeover. Collect interruption touch-gap evidence before choosing any TTL.

## Remaining work

- Finish full validation of fresh current-main v0.4.6 restage PR #280.
- Perform the final planned chat-to-chat handoff gate using this same real task ID and terminal Heartbeat done without a server restart.
- Record v0.4.6 acceptance, merge the fresh restage, and preserve v0.4.5 rollback.
- Implement observation-only same-card liveness: heartbeat_touch, last_executor_touch_at, last_ui_seen_at, and an executor freshness/status row.
- Run a deliberate frontend-interruption observation and measure executor-touch behavior before choosing any lease TTL.
- Only after measurement consider expired-owner takeover.

## Blockers / gates

- Do not implement or deploy the liveness layer until Workspace Heartbeat v0.4.6 PR #155 passes its remaining short-card, six-plus-update, and planned handoff live-host gates and is durably merged.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-executor-liveness-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.

## 2026-10-23 receiving-chat checkpoint

Planned cross-chat handoff PASS using the same task ID without server restart. v0.4.6 was merged through fresh restage PR #280 at `cd396157d7e3e5c3f955c15e41bebba501057693`. Observation-only liveness work is separately staged as v0.4.7; automatic takeover remains disabled.
