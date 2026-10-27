<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-secure-mcp-tunnel-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-secure-mcp-tunnel-v1
- Title: Workspace Heartbeat Secure MCP Tunnel & Bandwidth v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Preserve the accepted Workspace Heartbeat executor-liveness UX, including the approximately one-second live-card freshness poll and silent executor-touch signal, while removing the free-ngrok bandwidth/availability dependency. Measure the actual Heartbeat traffic path and payload costs, migrate ChatGPT-to-Lambda MCP transport to OpenAI Secure MCP Tunnel if the supported product path satisfies the security and capacity requirements, minimize unnecessary bytes without weakening liveness semantics, and retire the public ngrok endpoint only after an isolated and reversible live acceptance.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-heartbeat-secure-mcp-tunnel-v1-current-main
- Remote checkpoint: 8f7fd9f1cb05018aec840b8e3f0cb48d59708e64
- Remote verified: true

## Next safe action

Operator: create a dedicated Runtime API key in the OpenAI Platform organization for the principal that has Tunnels Read + Use on tunnel_6ae017d8655c8191976ef3bccc31f593. Do not paste the key into chat. Once created, start an isolated exact v0.4.8 Heartbeat loopback endpoint, initialize a tunnel-client profile targeting that local /mcp URL and the provisioned tunnel ID, inject CONTROL_PLANE_API_KEY locally via hidden input/environment, then run tunnel-client doctor --profile ... --explain and report only non-secret status/output.

## Remaining work

- Verify current official OpenAI Secure MCP Tunnel setup requirements and inspect Lambda for tunnel-client/configuration state without modifying production Heartbeat.
- Configure and validate an isolated outbound-only Secure MCP Tunnel profile targeting a private local v0.4.8 Heartbeat endpoint; do not expose a new public Lambda listener.
- Perform live ChatGPT acceptance through Secure MCP Tunnel for model tools, embedded app resource delivery, heartbeat_poll freshness, executor/semantic/card separation, and five/six-entry UI behavior.
- Only after acceptance, replace ngrok in the normal launcher path while preserving an operator-understandable rollback/emergency fallback and synchronize final task state.

## Blockers / gates

- A dedicated runtime API key still must be created locally for the tunnel-client daemon; its principal needs Tunnels Read + Use for tunnel_6ae017d8655c8191976ef3bccc31f593.
- The runtime key must not be pasted into chat, committed, or written into durable task files.
- Isolated v0.4.8 tunnel profile/doctor/run and live ChatGPT connector/app acceptance remain unverified.
- Public ngrok remains quota-blocked from ChatGPT; keep accepted production v0.4.7 :8787 and rollback intact until Secure MCP Tunnel acceptance passes.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-secure-mcp-tunnel-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
