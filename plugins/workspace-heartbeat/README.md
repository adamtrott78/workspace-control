# Workspace Heartbeat plugin

> **Runtime contract note:** the checked-in plugin source on this branch is historical and is not the accepted live ChatGPT delivery contract. The live Lambda service is Workspace Heartbeat v0.4.3. Executors must follow `procedures/progress_heartbeat.md` for the current operating contract. In particular, establish the live main-chat card with `heartbeat_open(task_id)`; if that card is later absent/unmounted/failed, a recovery `heartbeat_open(task_id)` is allowed.

MCP plugin for operator-visible progress during long-running workspace-control tasks.

## What it does

- `heartbeat_update(task_id, message, state)` appends one natural-language heartbeat to the owning task.
- `heartbeat_get(task_id?)` returns the latest heartbeat plus a bounded in-memory history.
- A ChatGPT thread/conversation panel polls `heartbeat_get` and updates one persistent panel in place.
- `task_id` is the stable progress identity across ChatGPT model/app session differences and chat handoffs.
- ChatGPT's anonymized `_meta["openai/session"]` remains useful for resolving an omitted task ID, but it is not the authority for stored heartbeat state.
- The server assigns monotonically increasing sequence numbers per task while the server process is alive.
- The panel retains up to 50 ordered updates and never clears a known-good heartbeat merely because a later poll is empty or fails.

Heartbeat text is intentionally normal prose. Structured fields exist only for routing and UI state.

## Runtime

Node.js 20 or newer is required.

```bash
cd plugins/workspace-heartbeat
npm install
npm test
npm start
```

The MCP endpoint is:

```text
http://localhost:8787/mcp
```

Successful MCP requests are logged with method, status, and latency.

## Current state model

Heartbeat history is bounded and in memory only. Restarting the server clears server-side history. The ChatGPT widget also persists its last rendered task/history through widget state when the host preserves that state.

The panel does **not** automatically reset to IDLE when a new assistant response begins because the MCP App does not have a reliable assistant-response-start lifecycle signal. It keeps the last known heartbeat visible until a newer heartbeat arrives. This avoids transient false-IDLE states.

## Connect to ChatGPT

Expose the server over HTTPS, add the resulting `https://.../mcp` endpoint as a custom MCP plugin, then open the Workspace Heartbeat thread panel in a normal Chat conversation.

For substantial long-running work:

1. use the owning workspace-control task ID consistently across chat handoffs;
2. write natural-language progress with `heartbeat_update`;
3. perform at most three subsequent non-heartbeat tool operations;
4. update the heartbeat again before tool operation four;
5. update immediately when diagnosis, scope, milestone, wait state, recovery point, or closure decision changes.

Do not replace normal reasoning with rigid status-card prose.
