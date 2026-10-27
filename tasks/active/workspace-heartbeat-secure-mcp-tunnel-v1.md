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

Restore only the previously verified production v0.4.7 Heartbeat runtime on :8787 using the existing operator launcher, verify exact source 9e5858738a4fd11801510e2839b0f94f19541506 and Node v20.20.2, then identify the existing :8788 listener without killing unknown processes. Run the exact def7c5fe6498b1bd742d912c1490d1f7160cab5f v0.4.8 candidate on a free isolated port and complete no-change/delta/resync payload measurements. Do not deploy v0.4.8 live or retire ngrok yet.

## Remaining work

- Validate the exact restaged v0.4.8 candidate with the Workspace Heartbeat Node test suite and workspace-control PR validation.
- Run the candidate on isolated Lambda :8788 and measure no-change, one-delta, resync, and 50-history routine heartbeat_poll response sizes while confirming live :8787 remains unchanged.
- Configure and validate an isolated outbound-only OpenAI Secure MCP Tunnel profile without exposing a new public Lambda endpoint.
- Perform live ChatGPT acceptance through Secure MCP Tunnel for model tools, app resource delivery, heartbeat_poll freshness, executor/semantic/card separation, and five/six-entry UI behavior.
- Only after acceptance, replace ngrok in the normal launcher path while preserving an operator-understandable rollback/emergency fallback and synchronize final task state.

## Blockers / gates

- Isolated post-change heartbeat_poll payload benchmark remains incomplete because TCP :8788 was already occupied; identify the listener and use a free isolated port without touching unrelated processes.
- Production v0.4.7 :8787 was manually stopped with heartbeat-down during the interrupted rerun and must be restored to the previously verified v0.4.7 runtime before continuing acceptance.
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
