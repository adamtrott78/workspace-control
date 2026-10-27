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
- Remote branch: workspace-heartbeat-secure-mcp-tunnel-v1
- Remote checkpoint: 95b8181aef3adda9a8c7ee52b694cd3096e8d826
- Remote verified: true

## Next safe action

Start from workspace-control main and the existing workspace-heartbeat-executor-liveness-v1 capsule. Recover exact live Heartbeat runtime/launcher provenance on Lambda without restarting it solely for discovery. Map the traffic paths: distinguish heartbeat_touch model tool calls from the approximately one-second live-card/app snapshot poll and any other requests to the public ngrok endpoint. Measure or tightly bound bytes/request and estimate monthly traffic before attributing the 1.02 GB incident. In parallel, verify the current official OpenAI Secure MCP Tunnel setup and limits. Then freeze a bounded outbound-only migration plan that preserves the one-second executor/card freshness UX and existing Heartbeat semantics. Do not touch GitRunner, automatic takeover, or unrelated workspace-control authority. Do not expose a new public Lambda endpoint.

## Remaining work

- Recover the exact current live Heartbeat runtime source SHA, Node/package version, launcher, localhost MCP endpoint, ngrok startup path, and rollback artifacts on Lambda.
- Trace the one-second card/server polling path and distinguish it from heartbeat_touch/model tool calls; measure or bound bytes per request/response and estimate monthly transfer.
- Inspect current official OpenAI Secure MCP Tunnel setup, authentication, supported custom-MCP path, request/payload/session limits, and operational requirements.
- Freeze an outbound-only migration and rollback design that preserves one-second freshness and accepted liveness semantics.
- Implement only the minimal payload/transport changes justified by measurement; keep historical/task-wide data off the high-frequency poll path.
- Run existing Heartbeat test suite plus workspace-control validation and isolated Lambda startup/transport tests.
- Perform live ChatGPT acceptance through Secure MCP Tunnel, including executor/card/semantic signal separation and one-second freshness.
- Retire ngrok from the normal Heartbeat path only after the Secure MCP Tunnel path is accepted; document rollback/emergency fallback.

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
