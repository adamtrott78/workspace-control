<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: `tasks/active/workspace-heartbeat-plugin-v1.json`

If this view disagrees with the JSON capsule or verified Git/runtime evidence,
trust the capsule plus verified evidence.

## Task

- ID: `workspace-heartbeat-plugin-v1`
- Status: **COMPLETE**
- Accepted design: Workspace Heartbeat **v0.4.3**
- Implementation checkpoint: `d7e692171c93f96adf7a70c6a1e514113a18075e`
- Branch: `heartbeat-v2-smoke-checkpoint`
- PR: #69
- Lambda runtime: `workspace-heartbeat-runtime-v043`

## Accepted operating contract

1. Start the Lambda heartbeat service with `heartbeat-up`.
2. During sustained ChatGPT work, write the first natural progress update with
   `heartbeat_update(task_id, message, state)`.
3. Call `heartbeat_open(task_id)` exactly once near the beginning.
4. Continue data-only `heartbeat_update` calls at meaningful state changes and
   before the fourth non-heartbeat tool operation.
5. Do not reopen/render the card. The existing iframe calls app-only
   `heartbeat_snapshot(task_id)` and keeps the same rolling-three card fresh.
6. Use `heartbeat_get(task_id)` only for explicit full task-local history.
7. Mark the final heartbeat `done` when the owning task actually completes.

`heartbeat_render` is retired. Native commentary is not the guaranteed
heartbeat delivery path.

## Live acceptance evidence — 2026-10-06

The user directly observed the same original card updating multiple times while
later GitHub/tool operations continued. The card rolled to the newest three
task-local heartbeats, changed to DONE, and required no second open/render call.

The user also verified the operator-local startup helper contains:

```text
DIR="/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v043/plugins/workspace-heartbeat"
```

Therefore the normal operator startup command is simply:

```bash
heartbeat-up
```

Changing that runtime target requires fresh runtime and live-host validation.

## Closure

The heartbeat side project is complete. Resume:

`tasks/active/workspace-lambda-github-tooling-optimization-v1.json`

Do not reopen heartbeat design work absent a new functional regression or
explicitly authorized runtime change.


## 2026-10-06 v0.4.4 policy-research checkpoint — NOT IMPLEMENTATION APPROVAL

Field evidence exposed a lifecycle problem rather than a v0.4.3 live-card
implementation failure:

- a card can self-refresh correctly while its iframe remains mounted;
- later assistant turns may keep writing backend/task history while the prior
  main-chat card is no longer the live current-turn surface;
- old existing chats may retain stale plugin/tool/UI metadata after plugin
  changes.

The current best candidate is **assistant-turn-scoped Heartbeat**:

1. `heartbeat_begin_turn(task_id, message, state)` is the single model-visible
   turn-boundary operation.
2. It atomically supersedes the prior active heartbeat turn for that
   conversation/task, creates a server-generated immutable `turn_id`, writes
   the first heartbeat, and mounts the new rolling-three card.
3. Later `heartbeat_update(task_id, message, state)` writes resolve to the
   current turn for that conversation/task.
4. The mounted app calls app-only
   `heartbeat_snapshot(task_id, turn_id)`; the immutable turn ID prevents old
   cards from displaying a newer assistant turn.
5. A superseded turn returns `active=false`/`superseded=true`; its old card
   stops polling and remains historical/static.
6. `heartbeat_get(task_id)` remains explicit task-level history/debugging and
   may span turns.
7. Policy still requires one active writer per durable task; turn isolation is
   defense-in-depth, not permission for concurrent ownership.

Candidate invariant:

`exactly one active heartbeat turn per (conversation, task_id)`.

The user explicitly does not need old-turn cards to stay live and prefers one
current rolling card for the assistant response being generated now.

**Do not implement yet.** Research current OpenAI/MCP Apps lifecycle contracts
and similar implementations first. If a documented native assistant-turn
identity or lifecycle exists, prefer it over inventing unnecessary state.
Otherwise validate or improve the server-generated `turn_id` design.

The accepted live v0.4.3 runtime remains the rollback/current production
implementation during this research.


## 2026-10-06 research review — candidate refined, still no implementation

External protocol review supports assistant-turn/run scoping. The strongest analogue
is AG-UI's durable `threadId` plus per-run `runId`, with run-start/run-finish
boundaries. OpenAI's Agents SDK likewise separates persistent session history
from each `Runner.run(...)` execution.

The candidate is refined as follows:

- `heartbeat_begin_turn(task_id, message, state)` atomically supersedes the
  previous active Heartbeat turn, generates an opaque server-owned `turn_id`,
  writes the first heartbeat, and mounts the current rolling-three card.
- The returned `turn_id` is **explicitly required** on every later
  `heartbeat_update(task_id, turn_id, message, state)`.
- Do not rely on `_meta["openai/session"]` as the update-routing key. Use it only
  to verify conversation ownership / reject cross-chat conflicts.
- The app calls
  `heartbeat_snapshot(task_id, turn_id)`; the response includes whether that
  turn remains active or has been superseded.
- A superseded card stops polling and remains static historical transcript UI.
- `heartbeat_get(task_id)` remains explicit task-level history/debugging across
  turns.
- `_meta["openai/widgetSessionId"]` is useful only for diagnostics of one
  mounted UI instance; it is not the turn identity.
- MCP `progressToken`/progress notifications are not suitable because they are
  scoped to one outstanding MCP request.
- MCP Tasks are not suitable as the primary mechanism because they represent one
  server-side asynchronous MCP request, not an assistant response that reasons
  across multiple unrelated tool calls.
- MCP Apps `ui/resource-teardown` can clean up a widget but correctness must not
  depend on teardown reaching the server; the next begin-turn supersedes old
  state deterministically.
- After changing Heartbeat tool/schema/UI metadata, refresh the plugin and start
  a **new conversation**. Existing conversations may retain stale tool/UI
  definitions and are unsupported for the upgraded contract.
- Preserve one active writer per durable task. A begin-turn arriving from a
  different ChatGPT conversation should fail closed unless a future explicit
  user-authorized takeover mechanism is designed.

The live v0.4.3 runtime remains untouched and is the rollback production path.

Next action is user review/freeze of this exact policy, then implementation.
