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

Continue ordinary research work with Workspace Heartbeat v0.2 enabled. The fresh-chat single-heartbeat retention smoke has passed, so do not repeat it. Wait for a naturally long/tool-heavy research turn that emits at least a second heartbeat, then visually verify the existing first entry remains, the new entry appends chronologically, the footer reports 2+ retained updates, and no false-IDLE transition occurs. Only that multi-heartbeat accumulation check remains before closing the panel-stability correction.

## Remaining work

- Keep the current v0.2 Lambda service and custom MCP plugin configuration unchanged.
- Use ordinary research work as the next smoke; do not manufacture extra tool calls solely to force a heartbeat.
- When a sufficiently long response naturally emits a second or later heartbeat, verify prior entries remain visible and the footer increases from 1 retained update to 2+ retained updates.
- Verify the newest heartbeat controls WORKING / WAITING / BLOCKED / DONE while earlier entries remain in chronological order.
- If multi-heartbeat accumulation passes without false IDLE or erasure, mark panel_stability_correction VALIDATED and close this heartbeat task.
- If history still disappears or resets, capture the visible footer/state plus MCP request log before changing implementation.

## Blockers / gates

- Final live validation is blocked only on observing a naturally long/tool-heavy research turn that emits at least two v0.2 heartbeats for the same owning task.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-plugin-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
