<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-plugin-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-plugin-v1
- Title: Workspace Heartbeat MCP Plugin v1
- Status: BLOCKED_RUNTIME
- Capsule schema: v2

## Goal

Build and validate a minimal MCP heartbeat tool plus ChatGPT conversation-panel UI so long-running workspace-control tasks can publish natural-language progress through a real tool call into one continuously updating side panel.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 3214ec2be4f0c20933784b3d265386d9652dfd0b
- Remote verified: true

## Next safe action

Continue ordinary research work with Workspace Heartbeat v0.2 enabled, but treat the heartbeat system as not yet stable. If heartbeat_update returns UNAVAILABLE again, immediately capture the MCP tmux window and ngrok request log around the failure before restarting or modifying anything; use those logs to classify whether the request reached the tunnel/server. If multiple heartbeats instead deliver successfully in one long turn, also verify chronological accumulation and non-erasure. Do not repeat the already-passed single-heartbeat retention test.

## Remaining work

- Keep the current v0.2 Lambda service and custom MCP plugin configuration unchanged until the intermittent UNAVAILABLE boundary is observed with transport evidence.
- On the next heartbeat UNAVAILABLE, capture the Workspace Heartbeat MCP console request/error lines and the ngrok request lines covering the failure before restarting or changing anything.
- If a subsequent long/tool-heavy turn successfully emits multiple heartbeats, verify earlier entries remain visible, the footer increases to 2+ retained updates, and the newest state controls the panel.
- Classify UNAVAILABLE only after correlating ChatGPT tool failure with MCP/ngrok evidence; do not assume a server, tunnel, or UI cause from the model-visible error alone.
- Close the heartbeat task only after both delivery availability and multi-heartbeat chronological accumulation are proven stable.

## Blockers / gates

- Heartbeat v0.2 end-to-end availability is intermittently failing: a later heartbeat_update returned UNAVAILABLE after earlier successful deliveries.
- Multi-heartbeat chronological accumulation remains unproven because the qualifying long turn has not yet produced two successfully delivered v0.2 heartbeat updates.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-plugin-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
