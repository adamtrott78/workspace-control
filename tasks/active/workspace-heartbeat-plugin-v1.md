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
- Remote checkpoint: f542f3bed7a3555877eb7bff14a38b13a4921692
- Remote verified: true

## Next safe action

Validate the v0.3 event-driven/adaptive correction at f542f3bed7a3555877eb7bff14a38b13a4921692 through workspace-control PR #69. If CI passes, merge it, deploy the canonical commit to the Lambda, restart workspace-heartbeat, load panel-v3.html in ChatGPT, and first verify the idle MCP request rate is no longer approximately one POST per second. Then resume the normal multi-heartbeat stability smoke.

## Remaining work

- Run workspace-control validation on PR #69 with the v0.3 source and synchronized task state.
- If validation passes, merge the exact PR head and sync the Lambda workspace-control checkout to the canonical merge.
- Restart workspace-heartbeat so server v0.3 and panel-v3.html are served.
- Recreate or refresh the ChatGPT custom MCP plugin if needed so the panel-v3 resource is loaded.
- With the panel open and otherwise idle, verify MCP request volume drops sharply from the v0.2 approximately one-request-per-second stream.
- Resume normal research work and verify multiple heartbeats append chronologically without false IDLE, erasure, or UNAVAILABLE.
- Close the task only after both request-rate/availability and multi-heartbeat history pass.

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
