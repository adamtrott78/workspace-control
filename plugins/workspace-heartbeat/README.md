# Workspace Heartbeat plugin

## v0.4.5 candidate — semantic cadence + full current-turn history

v0.4.5 preserves the accepted v0.4.4 turn lifecycle and changes two bounded
surfaces:

1. the MCP model instructions now match the canonical semantic-delta policy:
   meaningful changes drive updates, while 10 non-Heartbeat tool operations are
   only an anti-silence backstop;
2. the live in-chat card renders the full bounded history for the current
   assistant turn in one scrollable card instead of displaying only the latest
   three updates.

The lifecycle remains unchanged:

- call `heartbeat_begin_turn(task_id, message, state)` exactly once per
  substantial assistant response;
- carry the returned opaque `turn_id` on every later
  `heartbeat_update(task_id, turn_id, ...)` in that response;
- a later assistant response supersedes the prior turn;
- stale, completed, wrong-task, and cross-conversation updates fail closed;
- terminal `done` releases task ownership;
- `heartbeat_get(task_id)` remains explicit task-level history/sidebar
  inspection.

### Snapshot compatibility

`heartbeat_snapshot(task_id, turn_id)` now returns:

- `turn_history`: the bounded full history for exactly that immutable turn
  (default server bound: 50);
- `recent`: the existing latest-three compatibility projection;
- active/superseded/completed state.

The live card prefers `turn_history` and falls back to `recent` if connected
to an older compatible server. It validates every rendered item against the
card's immutable `task_id + turn_id`.

### Live-card behavior

The current-turn history region is bounded and scrollable. New updates
auto-follow only while the operator is already near the bottom; if the operator
has scrolled upward to read earlier updates, refreshes do not force the viewport
back to the newest entry.

Prior assistant turns never enter the current card. Superseded/completed cards
stop polling and remain static transcript history.

### Runtime

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

The accepted v0.4.4 Lambda runtime remains rollback until v0.4.5 passes exact
Node tests, isolated startup, live cutover, and ChatGPT host acceptance.

### Release boundary

This release changes MCP structured output and the live UI resource, so it is a
plugin-boundary release. Use the established lifecycle:

1. validate the exact candidate;
2. deploy it to an isolated runtime first;
3. preserve v0.4.4 rollback;
4. switch the managed runtime only after the isolated gate passes;
5. recreate/refresh the custom Heartbeat connection if needed and fully refresh
   the browser;
6. verify the actual tool surface/resource;
7. run a live turn with at least five semantic updates and confirm all remain
   readable in the same scrollable current-turn card.
