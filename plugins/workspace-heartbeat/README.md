# Workspace Heartbeat plugin

MCP plugin for operator-visible progress during long-running workspace-control tasks.

## Current accepted production contract — v0.4.3

v0.4.3 passed live ChatGPT host acceptance on 2026-10-06.

- `heartbeat_update`: model-visible, data-only natural progress write.
- `heartbeat_open(task_id)`: model-visible, called **once early** after the
  first update to mount one live task-scoped card.
- `heartbeat_snapshot(task_id)`: app-only, read-only latest-three projection
  called by the mounted iframe through MCP Apps `tools/call`.
- `heartbeat_get(task_id)`: explicit full task-local history/sidebar read.

The same mounted card was observed advancing repeatedly while later GitHub/tool
operations continued, rolling its visible history to the newest three updates,
then transitioning to DONE without any second open/render call.

### Lambda operator startup

The normal operator command is:

```bash
heartbeat-up
```

The accepted operator-local helper at `~/bin/heartbeat-up` currently uses:

```text
DIR="/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v043/plugins/workspace-heartbeat"
```

It owns the managed `workspace-heartbeat` tmux runtime and the existing ngrok
endpoint. If the helper's runtime target changes, run the plugin test/startup
gates before relying on the new target.


## What it does

- `heartbeat_update(task_id, message, state)` appends one natural-language heartbeat to the owning task.
- `heartbeat_get(task_id?)` returns the latest heartbeat plus a bounded in-memory history.
- A ChatGPT thread/conversation panel displays full task-local history on explicit `heartbeat_get`; it does not automatically poll.
- `task_id` is the stable progress identity across ChatGPT model/app session differences and chat handoffs.
- ChatGPT's anonymized `_meta["openai/session"]` remains useful for resolving an omitted task ID, but it is not the authority for stored heartbeat state.
- The server assigns monotonically increasing sequence numbers per task while the server process is alive.
- The panel retains up to 50 ordered updates for the selected task, and clears cached entries when explicitly switching to another task.

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


## v0.4.0 in-chat heartbeat cards

The primary operator UX is now the in-chat heartbeat update itself.

- `heartbeat_update` uses a dedicated UI resource and returns only the newest heartbeat object.
- Each update therefore renders one compact in-chat card containing only that heartbeat; task history and conversation timeline are not replayed into every update card.
- `heartbeat_get` retains the separate history/sidebar resource for explicit history inspection.
- This intentionally decouples reliable in-chat progress delivery from the host sidebar's mounted live-refresh lifecycle.
- The update card is stateless beyond the invoking heartbeat result, so a new chat does not inherit prior update-card contents.


## v0.4.1 chronology-first heartbeat delivery

ChatGPT owns placement of inline MCP App surfaces. Current inline UI is host-positioned before the generated model response, so a custom heartbeat card cannot be forced to remain at the exact point where the model invoked the tool.

To preserve operator chronology:

- `heartbeat_update` is now a data-only MCP tool with no `_meta.ui.resourceUri`.
- Its normal MCP `content` contains the heartbeat prose itself followed by task ID, sequence, and state.
- This keeps heartbeat state on the ordinary tool-result path, but field evidence showed ChatGPT may still collapse the result into a generic tool row instead of displaying the heartbeat prose inline.
- `heartbeat_get` remains the explicit rich history/sidebar surface at `ui://workspace-heartbeat/panel-v7.html`.
- The v0.4.0 update-card resource remains historical source but is no longer bound to routine heartbeat updates.
- No background polling, reconciliation timer, or duplicate render tool is introduced.


## v0.4.2 compact task summary

Long-turn stress testing showed that native assistant commentary is not preserved reliably deep into large tool sequences, while MCP tool calls continue to execute. v0.4.2 therefore stops requiring native commentary mirrors.

Routine delivery now has three distinct roles:

- `heartbeat_update` is data-only and records natural-language progress throughout the turn.
- `heartbeat_render(task_id)` is called **once near the end of a substantial turn** and renders one compact card containing only the latest three updates for that exact task.
- `heartbeat_get(task_id)` remains the explicit full-history/sidebar surface.

The summary card never mixes tasks and never replays the full history. The side panel now renders task-local `history` rather than preferring the cross-task `timeline`.

### Natural heartbeat prose

Heartbeat messages should sound like normal ChatGPT progress commentary, not telemetry.

Good:

> The runner reached checkout cleanly, but dependency setup failed before tests started. I’m isolating that path before changing the candidate code.

Avoid:

> Heartbeat 7: GitHub job read completed; continuing the validation sequence.

Messages should normally be one or two conversational sentences focused on a meaningful finding, decision, state change, or next action. Structured metadata already carries task ID, state, sequence, and timestamp, so prose does not need to repeat them.

The rolling-card window is three updates for v0.4.2. Full bounded task history remains available through the side panel.


## v0.4.3 — one self-refreshing task card (accepted)

**Field evidence:** v0.4.2 `heartbeat_render` displayed late and produced a separate immutable snapshot on every call. A mid-turn render with updates 1–2 did not receive subsequent updates; a second end-turn render displayed only 5–7 in a separate card. Therefore `heartbeat_render` is removed.

Updated responsibilities:

1. `heartbeat_update(task_id, message, state)` remains data-only and records conversational semantic progress.
2. After the first update, the model calls **`heartbeat_open(task_id)` once early** to mount a single task-scoped card. The host still controls when initial mounting occurs.
3. The mounted app initializes the MCP Apps JSON-RPC bridge and calls an **app-only, read-only** `heartbeat_snapshot(task_id)` through `tools/call`.
4. While visible and working, it refreshes after 1.5 seconds; waiting/blocked states use 3.5 seconds. Each reply replaces the same card's DOM, showing only the most recent **three task-local updates**. Failed requests back off without clearing the last known state; hidden widgets pause; done widgets stop.
5. `heartbeat_get(task_id)` continues to show the bounded full history for that task through the separate explicit side panel.

`heartbeat_snapshot` is declared `_meta.ui.visibility: ["app"]` and `readOnlyHint: true`. It never returns cross-task timeline data. UI scripts use MCP Apps `ui/initialize` / `ui/notifications/initialized` and `tools/call`, never direct HTTP from the iframe.

ChatGPT still controls initial resource placement, but live host acceptance passed on 2026-10-06: one early-mounted card visibly refreshed in place through repeated later heartbeat_update calls, rolled to the newest three messages, and reached DONE without a second open/render call. Unit tests additionally cover the bridge contract, rolling window, isolation, hidden pause, and terminal-state stop.

Side-panel isolation tightening for v0.4.3: widget state is filtered to the active task on load; changes of explicit tool input/result task ID reset the cached view before merging. History from other tasks can never appear in this task's panel.
