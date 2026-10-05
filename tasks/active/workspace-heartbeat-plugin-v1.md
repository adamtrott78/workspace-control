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
- Remote checkpoint: 3487c55f6cc604eb046547d419c7511544ac256f
- Remote verified: true

## Next safe action

On the user's machine, sync workspace-control main to 3487c55f6cc604eb046547d419c7511544ac256f, then run the bounded local developer-mode smoke from plugins/workspace-heartbeat: npm install; npm test; npm start; inspect http://localhost:8787/mcp with MCP Inspector; expose port 8787 through an HTTPS development tunnel; add the resulting https://.../mcp endpoint in ChatGPT Developer mode; open the thread conversation panel; invoke heartbeat_update twice and confirm one panel updates in place. Return exact npm/Inspector/tunnel/ChatGPT evidence. Do not add persistence/auth/hosting/history/SSE before this smoke.

## Remaining work

- On the user's machine, fast-forward workspace-control main to the canonical MVP checkpoint and enter plugins/workspace-heartbeat.
- Run npm install, npm test, and start the MCP server.
- Verify the local MCP endpoint with MCP Inspector.
- Expose port 8787 through an HTTPS development tunnel.
- Enable ChatGPT Developer mode, add the HTTPS /mcp endpoint as a personal plugin, and open the thread panel beside a test conversation.
- Call heartbeat_update twice and verify the same panel box updates in place with increasing sequence numbers.
- Only after the live smoke succeeds, decide whether persistence, OAuth, public hosting, history, or push events are warranted.

## Blockers / gates

- Live panel smoke requires a human-accessible local runtime plus ChatGPT Developer-mode MCP connection; this executor cannot create the user's local tunnel or install the custom MCP connection on their behalf.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-plugin-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
