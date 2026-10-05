# Workspace Heartbeat plugin

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


## v0.3.1 delivery model

The panel is event-driven only.

- Model-initiated heartbeat results arrive through the MCP Apps `ui/notifications/tool-result` lifecycle.
- Existing state hydrates from the tool result and persisted widget state when the panel mounts.
- The panel does not automatically call `heartbeat_get`, does not run a timer, and does not poll in the background.
- `heartbeat_get` remains available for explicit model/user reconciliation when needed.

This removes both the v0.2 one-second polling loop and the v0.3 five-second fallback reconciliation that still produced recurring transport traffic.


## v0.3.2 mounted-panel delivery

Both heartbeat tools are associated with the same UI resource URI.

- `heartbeat_get` remains the only tool that advertises the thread sidebar entrypoint.
- `heartbeat_update` now also declares `_meta.ui.resourceUri` for the same panel resource so ChatGPT can route model-initiated update results to an already-mounted heartbeat app.
- The panel remains event-driven only: no timer, background polling, or automatic `heartbeat_get` calls.
- The resource key is bumped to `panel-v5.html` so the updated tool/UI association is rediscovered cleanly.


## v0.3.3 cross-task operator timeline

Task-local history remains authoritative for task APIs, while the mounted operator panel renders a bounded conversation timeline across task ownership changes.

- Heartbeats keep per-task sequence numbers and task-local history.
- The store also maintains a bounded timeline for the model session producing updates.
- A task remembers its latest timeline so explicit task reads can recover the surrounding operator context even if app/model session metadata differs.
- The panel prefers `timeline` for display and shows task-boundary labels when ownership changes.
- This avoids making a parent-to-child durable task handoff look like lost heartbeat history.
- The panel remains event-driven only and does not reintroduce background polling.
