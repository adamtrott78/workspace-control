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
- Remote checkpoint: 9303ab5708e0622747e63601b0372e74521fd8a8
- Remote verified: true

## Next safe action

Validate and deploy Workspace Heartbeat v0.3.2. The key live test is now narrow: with panel-v5 mounted and left open, a model-initiated heartbeat_update must appear in the existing sidebar without closing/reopening it, while the idle panel remains free of recurring heartbeat_get traffic. Do not redesign heartbeat cadence: retained history already proves at least seven heartbeat updates were emitted during the long research turn; the earlier two-update appearance was a stale mounted-panel display problem.

## Remaining work

- Validate the final v0.3.2 PR #69 head through workspace-control CI once the unrelated research-engine task-contract state on main no longer invalidates the repository.
- Deploy the exact validated v0.3.2 head/canonical merge to the isolated Lambda heartbeat runtime and restart workspace-heartbeat.
- Recreate the ChatGPT custom plugin so the updated tool metadata and panel-v5.html resource are loaded.
- Keep the heartbeat sidebar open and allow ordinary research work to emit a new heartbeat_update; verify it appears live without closing/reopening the panel.
- Confirm there is still no recurring background heartbeat_get traffic while idle.
- Treat occasional isolated 400 responses during plugin/panel initialization separately from recurring application polling; investigate only if they correlate with failed heartbeat delivery.
- Close the heartbeat task after live mounted refresh, idle quietness, and normal heartbeat delivery all pass.

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
