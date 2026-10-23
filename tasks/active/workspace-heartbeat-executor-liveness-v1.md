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
- Remote branch: checkpoint-heartbeat-liveness-mvp-acceptance
- Remote checkpoint: 04852fe2111143a7950ccbdb15f3ed13b95a7521
- Remote verified: true

## Next safe action

Merge and validate the canonical heartbeat_touch emission-policy patch. After merge, use the <=3 non-Heartbeat-operation liveness backstop immediately in task chats; deploy/refresh the v0.4.7 runtime when convenient so server-delivered instructions match. Then collect one long-turn/frontend-interruption observation before considering TTL or automatic takeover.

## Remaining work

- Deploy/refresh the v0.4.7 runtime from the merged source when convenient so the MCP server-delivered instructions include the new touch cadence; the canonical workspace-control procedure is authoritative immediately after merge.
- Collect a deliberate long-turn / frontend-interruption field observation under the new touch-emission policy and record measured executor-touch gaps.
- Choose any recovery/takeover semantics only in a separate approved phase; automatic takeover remains disabled.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-executor-liveness-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
