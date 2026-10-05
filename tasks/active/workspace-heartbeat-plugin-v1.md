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
- Remote branch: workspace-heartbeat-plugin-v1
- Remote checkpoint: abdd2315af71748c9c369e4cb076981a9d214f54
- Remote verified: true

## Next safe action

Open a workspace-control PR for workspace-heartbeat-plugin-v1 and require repository validation on the exact branch head. If it passes, stop repository implementation and hand off one local developer-mode smoke sequence: npm install/test, MCP Inspector, HTTPS tunnel, ChatGPT Developer-mode connection, thread-panel open, and heartbeat_update in-place refresh verification. Do not add persistence/auth/hosting/history/SSE before that smoke.

## Remaining work

- Open and pass workspace-control PR validation for the exact MVP branch.
- After repository validation, run npm install/npm test and MCP Inspector on the user's Lambda or another local machine with network access.
- Expose the local MCP endpoint through an HTTPS development tunnel and connect it in ChatGPT Developer mode.
- Open the thread panel, call heartbeat_update from a test chat, and verify the same panel updates in place.
- Only after the developer-mode smoke succeeds, decide whether persistence, OAuth, public hosting, history, or SSE/event push are actually needed.

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
