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
- Remote branch: workspace-heartbeat-history-v2
- Remote checkpoint: 906478d671dc750b5c739a716fb32a1a650f0b0c
- Remote verified: true

## Next safe action

Open and validate the workspace-heartbeat-history-v2 correction at 906478d671dc750b5c739a716fb32a1a650f0b0c. After repository validation passes, merge it, update the Lambda to the canonical merge, restart heartbeat-up, reopen the custom MCP thread panel, and use the user's fresh research-engine handoff chat as the long stability smoke. The pass condition is not merely that a heartbeat appears: multiple task-scoped updates must remain in chronological history, the latest state must persist between updates, and empty/failed polls must never force a false IDLE or erase known-good progress.

## Remaining work

- Run workspace-control repository validation on workspace-heartbeat-history-v2.
- If validation passes, merge the correction and sync the Lambda checkout to the exact canonical commit.
- Restart the persistent workspace-heartbeat tmux service so server.js and the panel resource use v0.2.
- Refresh/reopen the Workspace Heartbeat custom MCP plugin/thread panel so ChatGPT loads panel-v2.html.
- Use the new research-engine handoff chat as a long rehydration smoke: emit several natural-language heartbeat_update calls under the same owning task_id.
- Verify old updates remain visible as a sequential log, the newest update remains WORKING/WAITING/BLOCKED/DONE as emitted, and the panel never switches to IDLE unless it has never received a heartbeat.
- Verify successful /mcp requests appear in the MCP tmux window.
- After the stability/history smoke passes, decide separately whether a future explicit turn-reset event is worth adding; do not fake assistant-response-start detection.

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
