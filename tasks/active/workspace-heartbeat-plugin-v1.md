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
- Remote checkpoint: fd615356972cbe1d306cca793c387badf2f7168a
- Remote verified: true

## Next safe action

Validate and deploy Workspace Heartbeat v0.3.3. The next live acceptance should exercise both fixes together: leave panel-v6 mounted, verify model-initiated heartbeat_update results appear without closing/reopening, and when ownership moves to a child durable task in the same chat, verify prior-task updates remain visible with a task-boundary label while child-task updates append. The panel must remain event-driven only with no recurring heartbeat_get polling.

## Remaining work

- Validate the final Workspace Heartbeat v0.3.3 PR #69 head through workspace-control CI.
- If validation passes, merge the exact head and deploy the canonical merge to the isolated Lambda heartbeat runtime.
- Restart workspace-heartbeat and recreate/refresh the custom MCP plugin so panel-v6.html and the v0.3.3 tool schema are loaded.
- With the sidebar left mounted, verify a new heartbeat_update appears live without close/reopen and no recurring background heartbeat_get traffic occurs.
- During a real durable task ownership change in the same research chat, verify prior-task heartbeats remain visible, a task-boundary label appears, and new-task heartbeats append to the same bounded operator timeline.
- Treat isolated 400 responses during plugin/panel initialization separately from recurring application polling; only investigate further if they correlate with failed heartbeat delivery.
- Close the heartbeat task after mounted live refresh, idle quietness, normal delivery, and cross-task timeline continuity all pass.

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
