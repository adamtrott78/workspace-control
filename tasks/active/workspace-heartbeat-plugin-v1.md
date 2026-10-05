<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-plugin-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-plugin-v1
- Title: Workspace Heartbeat MCP Plugin v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Build and validate a minimal MCP heartbeat tool plus ChatGPT conversation-panel UI so long-running workspace-control tasks can publish natural-language progress through a real tool call into one continuously updating side panel.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 838022e9af0feff8a07894863a96663a73dc9d83
- Remote verified: true

## Next safe action

With the Workspace heartbeat thread panel visibly open in normal Chat mode, invoke heartbeat_update once for the owning task and verify the panel changes from its idle state to the emitted natural-language message with sequence 1. Then invoke heartbeat_update a second time and verify the same panel updates in place to sequence 2. Treat model prose such as 'the panel is working' as non-evidence unless the user visibly observes the panel update. Successful MCP requests are not currently printed by server.js, so an empty MCP terminal is not evidence of no request; use the ngrok request log or add explicit request logging if transport proof is needed. Do not add persistence/auth/history/SSE before the update loop is proven.

## Remaining work

- In the live research chat with the Workspace heartbeat panel already open, invoke heartbeat_update for the owning task with a short natural-language working-state message.
- Verify the panel replaces its idle text with the new heartbeat and shows sequence 1.
- Invoke heartbeat_update again with different prose and verify the same panel updates in place to sequence 2 rather than creating another panel/card.
- Capture ngrok HTTP request evidence or add explicit server request logging if transport observability is still needed; do not infer successful delivery from an empty MCP terminal because successful requests are not currently logged.
- After the live update loop passes, add a bounded runtime preflight declaring Node >=20 so future startup fails clearly on unsupported Node 12.
- Only after the end-to-end update loop is proven, decide whether persistence/history/SSE/auth/public hosting are warranted.

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
