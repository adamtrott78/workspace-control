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

Resolve the actual Node child PID 1847970 executable/version and launcher ancestry read-only. Then run an isolated Heartbeat instance on a separate port using the verified runtime executable, measure heartbeat_snapshot serialized response bytes/cadence independently from model MCP calls at bounded history sizes, and only then test outbound-only Secure MCP Tunnel embedded app/resource behavior. Do not restart or mutate live :8787 for discovery.

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

- Live source/CWD/port/ngrok process and rollback presence are verified. Exact child Node executable/version, launcher ancestry, and measured per-poll bytes remain open.
- Secure MCP Tunnel tunnel ID/permissions/runtime key, embedded app resource delivery, app-only snapshot operation, and live ChatGPT acceptance remain unverified.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-secure-mcp-tunnel-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.

## 2026-10-26 verified discovery checkpoint

- Source audit confirms app-only `heartbeat_snapshot` sends full bounded `turn_history` on each poll; the checked-in card schedules 1500 ms while working and 3500 ms otherwise after response. `heartbeat_touch` remains model-only and silent.
- Official Secure MCP Tunnel defaults verified: outbound HTTPS; 600 MCP requests/minute, 10 MiB serialized envelope, 120-second deadline, 1,000 queued. Embedded live-card app behavior over that transport remains unproven.
- Heartbeat `begin_turn` attempt failed HTTP 403 at ngrok-free.dev. No new turn ID, host restart, or network cutover.
- Fresh operator inspection at 2026-10-26T21:49:27-04:00 verifies local Heartbeat HTTP 200 on 127.0.0.1:8787, `node server.js` child PID 1847970, ngrok PID 1847986 forwarding the fixed ngrok-free.dev domain to 8787, runtime CWD `workspace-heartbeat-runtime-v047/plugins/workspace-heartbeat`, exact checkout `9e5858738a4fd11801510e2839b0f94f19541506`, package v0.4.7, and v0.4.6 rollback directory presence.
- Login-shell Node is v12.22.9, but the prior probe captured launcher shell PID 1847969 rather than the Node child. Exact child executable/version and launcher ancestry remain to verify.
- See `procedures/workspace_heartbeat_secure_mcp_tunnel.md` for the current evidence and isolated acceptance plan.
- Next action: resolve child Node/launcher, then isolated payload measurement; no live :8787 restart or tunnel cutover.
