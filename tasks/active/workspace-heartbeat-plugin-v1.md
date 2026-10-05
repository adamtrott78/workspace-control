<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-plugin-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-plugin-v1
- Title: Workspace Heartbeat MCP Plugin v1
- Status: VALIDATING
- Capsule schema: v2

## Goal

Build and validate a minimal MCP heartbeat tool plus ChatGPT conversation-panel UI so long-running workspace-control tasks can publish natural-language progress through a real tool call into one continuously updating side panel.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: heartbeat-v2-smoke-checkpoint
- Remote checkpoint: ff9347f347540fbe0f2a20b8b5106e80dc4572e5
- Remote verified: true

## Next safe action

Validate the final event-driven-only Workspace Heartbeat v0.3.1 head on PR #69. After CI passes, merge and deploy the canonical commit, mount panel-v4.html, and verify that an idle open panel produces no recurring MCP heartbeat_get traffic while ordinary heartbeat_update calls still append promptly. Multi-heartbeat history itself is already proven PASS and must not be repeated as a prerequisite.

## Remaining work

- Validate the final event-driven-only v0.3.1 PR #69 head through workspace-control CI.
- If validation passes, merge the exact head and deploy the canonical merge to the Lambda heartbeat runtime.
- Restart workspace-heartbeat and recreate/refresh the custom MCP plugin so panel-v4.html is mounted.
- Open the panel and observe the MCP/ngrok console while idle; there must be no recurring background heartbeat_get traffic.
- Trigger ordinary research work with one or more heartbeat_update calls and confirm updates still append promptly through ui/notifications/tool-result without UNAVAILABLE.
- If idle request-rate and delivery availability pass, mark panel_stability_correction VALIDATED and close the heartbeat task.

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
