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
- Remote checkpoint: 7c63e518d470b4edf264406a2258d12394b950a4
- Remote verified: true

## Next safe action

Validate the exact v0.4.8 candidate restaged from current main on branch workspace-heartbeat-secure-mcp-tunnel-v1-current-main. Run the existing Workspace Heartbeat Node tests and workspace-control validation, then run an isolated :8788 post-change byte benchmark proving routine no-change heartbeat_poll responses are bounded and do not retransmit turn_history. Do not modify live :8787, reduce polling cadence, enable automatic takeover, expose Lambda publicly, or retire ngrok before isolated and live Secure MCP Tunnel acceptance.

## Remaining work

- Validate the exact restaged v0.4.8 candidate with the Workspace Heartbeat Node test suite and workspace-control PR validation.
- Run the candidate on isolated Lambda :8788 and measure no-change, one-delta, resync, and 50-history routine heartbeat_poll response sizes while confirming live :8787 remains unchanged.
- Configure and validate an isolated outbound-only OpenAI Secure MCP Tunnel profile without exposing a new public Lambda endpoint.
- Perform live ChatGPT acceptance through Secure MCP Tunnel for model tools, app resource delivery, heartbeat_poll freshness, executor/semantic/card separation, and five/six-entry UI behavior.
- Only after acceptance, replace ngrok in the normal launcher path while preserving an operator-understandable rollback/emergency fallback and synchronize final task state.

## Blockers / gates

- Exact v0.4.8 Node test suite, workspace-control validation, and isolated post-change payload benchmark are not yet complete; do not deploy the candidate to live :8787.
- Secure MCP Tunnel tunnel/workspace association, runtime authorization, embedded app resource delivery, app-only heartbeat_poll behavior, and live ChatGPT acceptance remain unverified; do not retire ngrok yet.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-secure-mcp-tunnel-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
