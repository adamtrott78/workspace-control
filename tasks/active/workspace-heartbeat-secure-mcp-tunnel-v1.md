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

Operator: press Ctrl-C in the temporary Secure MCP Tunnel acceptance terminal so no second tunnel-client polls tunnel_6ae017d8655c8191976ef3bccc31f593. Then fetch exact cutover head d9b6fb7232bf157beefc6bf30c894295422ef87f on Lambda and run scripts/workspace_heartbeat_secure_tunnel_cutover.sh as the normal atrott user. Enter the dedicated runtime key only if prompted. Paste the non-secret output. Do not invoke heartbeat_get for routine monitoring.

## Remaining work

- Verify current official OpenAI Secure MCP Tunnel setup requirements and inspect Lambda for tunnel-client/configuration state without modifying production Heartbeat.
- Configure and validate an isolated outbound-only Secure MCP Tunnel profile targeting a private local v0.4.8 Heartbeat endpoint; do not expose a new public Lambda listener.
- Perform live ChatGPT acceptance through Secure MCP Tunnel for model tools, embedded app resource delivery, heartbeat_poll freshness, executor/semantic/card separation, and five/six-entry UI behavior.
- Only after acceptance, replace ngrok in the normal launcher path while preserving an operator-understandable rollback/emergency fallback and synchronize final task state.

## Blockers / gates

- Production still runs accepted v0.4.7 on :8787 under the existing heartbeat-up launcher with ngrok as sibling transport.
- A production-safe v0.4.8 runtime, supervised tunnel-client launch path, restricted non-interactive secret reference, and rollback procedure must be implemented and validated before ngrok can leave the normal path.
- The temporary tunnel-backed acceptance plugin should remain available until the production cutover is proven.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-secure-mcp-tunnel-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
