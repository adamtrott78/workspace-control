# Workspace Heartbeat plugin

## v0.4.8 candidate — bandwidth-bounded live polling

v0.4.8 preserves the accepted v0.4.7 executor/semantic/card signal separation and the existing 1500 ms working / 3500 ms non-working live-card cadence, but removes full-history retransmission from the high-frequency path.

- `heartbeat_snapshot(task_id, turn_id)` remains available for bounded full-turn compatibility/debug hydration.
- The mounted live card now repeatedly calls app-only `heartbeat_poll(task_id, turn_id, after_sequence)`.
- A normal no-change poll returns turn/liveness state with an empty semantic `updates` array.
- Semantic entries are sent only when their sequence is newer than the card's last rendered sequence.
- If the card falls behind the retained turn-history window, the server returns a bounded resync payload containing only the retained current-turn window.
- Turn fencing, semantic history, silent `heartbeat_touch`, executor freshness, card/server freshness, grow-through-five/scroll-from-six behavior, hidden/teardown polling suspension, and stale-owner policy are unchanged.

This change is a plugin-boundary release because the app resource and tool schema change. Validate exact Node tests, isolated startup, measured response bytes, and Secure MCP Tunnel app/resource behavior before any live cutover.

v0.4.6 is a narrow live-card sizing hotfix on top of accepted v0.4.5. The turn lifecycle, semantic-delta policy, full bounded current-turn history, grow-through-five behavior, and scroll-from-six behavior are unchanged.

The hotfix changes only iframe resize measurement: `ui/notifications/size-changed` now reports the intrinsic rendered `<main>` card height rather than `document.documentElement.scrollHeight`. The latter is at least the current iframe viewport height and can therefore feed an oversized host allocation back to ChatGPT, leaving a large blank area below short one- or two-update cards.

The live resource is cache-busted to `live-v5.html`.

## v0.4.6 candidate — semantic cadence + full current-turn history

v0.4.6 preserves the accepted v0.4.4 turn lifecycle and changes two bounded
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
- terminal `done` closes the current Heartbeat turn and releases task ownership; it does not by itself mark the durable workspace task complete;
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

The current-turn card grows naturally through five Heartbeats and sends `ui/notifications/size-changed` so the host can resize the iframe. From update six onward, the history region stays at the measured five-entry height and scrolls internally.
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

The accepted v0.4.4 Lambda runtime remains rollback until v0.4.6 passes exact
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


### Durable chat-to-chat handoff

A durable workspace task can move from one ChatGPT conversation to another while
remaining in progress. The outgoing conversation must release Heartbeat's
volatile writer lease as part of that handoff.

For a planned handoff:

1. finish the outgoing conversation's required task mutations and validation;
2. synchronize the authoritative task capsule and any derived Markdown/handoff;
3. make the **final Heartbeat operation** in the outgoing conversation
   `heartbeat_update(task_id, turn_id, ..., state="done")`;
4. after releasing the Heartbeat turn, do not perform additional task mutations
   in the outgoing conversation; the final assistant text may present the
   already-prepared handoff prompt;
5. the receiving conversation resumes the original durable `task_id` and calls
   `heartbeat_begin_turn` normally in its first substantial response.

`state="done"` is scoped to the **Heartbeat turn/writer lease**. It means the
outgoing Heartbeat writer is finished. It does **not** mark the durable
workspace-control task `COMPLETE`, clear its remaining work, or authorize a
task-state transition by itself.

If the outgoing conversation becomes unreachable before it can release the
lease, and the receiving chat fails with
`HEARTBEAT_TASK_OWNED_BY_ANOTHER_CONVERSATION`, treat that as an orphaned
volatile Heartbeat owner. If the old conversation cannot be resumed to send
`done`, use the coordinated Heartbeat-server-only restart recovery below.
Never invent a replacement task ID and never weaken cross-conversation
ownership checks to force the handoff.

### Plugin refresh and stale ownership

Recreating or refreshing the custom Heartbeat plugin can change the
conversation/session identity supplied to the MCP server. If a task still has
an active pre-refresh Heartbeat turn, a resumed chat may fail closed with
`HEARTBEAT_TASK_OWNED_BY_ANOTHER_CONVERSATION`.

Close active turns with `state="done"` before plugin recreation where
practical. If the old owner is no longer reachable, coordinate a restart of
only the Workspace Heartbeat server/runtime to clear volatile in-memory
ownership/history, then resume with the task's original durable `task_id`.
Never invent a replacement task ID to bypass ownership.

The restart affects all volatile Heartbeat state in that server process but does
not mutate workspace-control task capsules, Git state, Lambda CI state, or other
durable workspace data.
