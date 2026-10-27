<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-secure-mcp-tunnel-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-secure-mcp-tunnel-v1
- Title: Workspace Heartbeat Secure MCP Tunnel & Bandwidth v1
- Status: COMPLETE
- Capsule schema: v2

## Goal

Preserve the accepted Workspace Heartbeat executor-liveness UX, including the approximately one-second live-card freshness poll and silent executor-touch signal, while removing the free-ngrok bandwidth/availability dependency. Measure the actual Heartbeat traffic path and payload costs, migrate ChatGPT-to-Lambda MCP transport to OpenAI Secure MCP Tunnel if the supported product path satisfies the security and capacity requirements, minimize unnecessary bytes without weakening liveness semantics, and retire the public ngrok endpoint only after an isolated and reversible live acceptance.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-heartbeat-secure-mcp-tunnel-v1-current-main
- Remote checkpoint: 1d373f8a3cd3d2ab7357b05b5b883b144b26d3ac
- Remote verified: true

## Next safe action

Task complete. Workspace Heartbeat production now runs exact v0.4.8 with OpenAI Secure MCP Tunnel as the normal transport, bounded delta polling, preserved 1500 ms/3500 ms card cadence, and explicit v0.4.7/ngrok rollback at /home/atrott/bin/heartbeat-rollback-v047-ngrok. Routine monitoring must not invoke heartbeat_get solely for progress because that renders a separate full-history panel; use begin/update/touch plus app-only heartbeat_poll. Any future transport, polling-semantics, automatic-takeover, or broader ingress change requires a separate reviewed task.

## Remaining work

- None.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-secure-mcp-tunnel-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
