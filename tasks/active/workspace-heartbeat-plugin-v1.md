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

On the Lambda, sync workspace-control main to 3214ec2be4f0c20933784b3d265386d9652dfd0b; stop and restart the workspace-heartbeat tmux service so v0.2 is actually running; verify heartbeat-status; refresh/reopen the Workspace Heartbeat thread panel; then use the user's new research-engine handoff chat as a long rehydration smoke. The pass condition is: multiple updates accumulate as a sequential log, the latest heartbeat remains visible between events, no empty/failed poll forces IDLE after valid state exists, and successful /mcp traffic is visible in the MCP console.

## Remaining work

- On the Lambda, fast-forward workspace-control main to 3214ec2be4f0c20933784b3d265386d9652dfd0b.
- Restart the persistent workspace-heartbeat tmux session so the server and panel use v0.2.
- Confirm heartbeat-status shows both MCP and ngrok UP, and that the MCP window logs successful /mcp requests.
- Refresh/reopen the Workspace Heartbeat thread panel so ChatGPT loads panel-v2.html.
- Start the fresh research-engine handoff chat with the Workspace Heartbeat plugin enabled and the owning workspace-control task ID reused consistently.
- During the lengthy rehydration, verify several heartbeat_update calls append in chronological order, the latest state remains visible between updates, and the panel never falls back to IDLE after valid progress exists.
- If the live smoke passes, mark panel_stability_correction VALIDATED and close this heartbeat task; defer any explicit turn-reset/IDLE lifecycle feature until there is a reliable response-start signal.

## Blockers / gates

- Live validation is blocked on the user-controlled Lambda/ChatGPT smoke: sync the canonical v0.2 commit, restart the persistent workspace-heartbeat service, reopen the thread panel, and exercise multiple heartbeats during fresh-chat rehydration.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-plugin-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
