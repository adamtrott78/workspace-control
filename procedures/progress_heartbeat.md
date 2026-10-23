# Operator Progress Heartbeat

Status: **Workspace Heartbeat v0.4.5 accepted; v0.4.6 live candidate under final host validation**

## Purpose

Long-running work must remain understandable to the human operator while it is
happening.

Heartbeat is the transport for concise, user-facing intermediate commentary
during substantial work. It should approximate the useful high-level reasoning
summary/preamble that an agent would naturally give the user while continuing
to work.

Heartbeat is **not** private chain-of-thought, scratch reasoning, telemetry, a
tool-call log, or a periodic status obligation.

A strong update usually communicates some natural combination of:

1. what was just learned, established, completed, or ruled out;
2. why that matters to the current diagnosis or plan;
3. what happens next and why.

Prefer causal language such as:

- "The failure is narrower than it looked: ..."
- "That rules out X, so I’m checking Y next."
- "The validation passed, which means ..."
- "This changes the plan because ..."
- "I’ve confirmed X; the remaining uncertainty is Y."

Usually use one or two concise sentences.

## Accepted ChatGPT Workspace Heartbeat delivery — v0.4.5 lifecycle

For each **substantial assistant response** using the connected Workspace
Heartbeat MCP plugin:

1. call `heartbeat_begin_turn(task_id, message, state)` exactly once, at the
   first point where a natural user-facing progress/commentary update is useful;
2. save the opaque server-generated `turn_id` returned by that call;
3. reuse that exact `turn_id` on every later
   `heartbeat_update(task_id, turn_id, message, state)` in the same assistant
   response;
4. **never call `heartbeat_begin_turn` a second time in the same assistant
   response**. A milestone, merge, checkpoint, validation phase, diagnosis
   change, operator handoff, or other internal phase transition does not create
   a new assistant turn;
5. a later assistant response may call `heartbeat_begin_turn` once for the
   same task. The server supersedes the prior active turn, and the old in-chat
   card becomes static historical UI;
6. the mounted current-turn card reads app-only
   `heartbeat_snapshot(task_id, turn_id)` and displays the full bounded
   current-turn `turn_history`; the compatibility `recent` field remains
   latest-three only;
7. use `heartbeat_get(task_id)` only for explicit task-history/sidebar
   inspection. It is not the routine live-progress path;
8. a terminal `heartbeat_update(..., state="done")` closes the active
   Heartbeat turn and releases the volatile task-writer lease. `done` is a
   Heartbeat lifecycle state, not evidence that the durable workspace task is
   `COMPLETE`;
9. use that terminal `done` as the final Heartbeat operation when either the
   durable task is actually complete **or** the current ChatGPT conversation is
   intentionally handing the still-active durable task to another conversation
   after its capsule/handoff state has been synchronized.

Missing, stale, superseded, wrong-task, or cross-conversation `turn_id` values
fail closed. `_meta["openai/session"]` is conversation-ownership evidence only;
it is not the turn-routing key.

### Exactly one begin-turn per assistant response

This is a hard lifecycle invariant.

After `heartbeat_begin_turn` succeeds, the returned `turn_id` remains the
Heartbeat identity for the entire assistant response, even if the work changes
phase multiple times.

Do not mentally equate any of the following with a new assistant response:

- implementation -> validation;
- validation -> merge;
- merge -> checkpoint;
- diagnosis -> correction;
- correction -> operator instruction;
- one subproblem -> another subproblem within the same response.

A new `heartbeat_begin_turn` is permitted only after the assistant has
actually sent its response to the user and a subsequent assistant response has
begun.

### Chat-to-chat durable task handoff

Conversation ownership is volatile Heartbeat state. Durable task state lives in
the task capsule and owning repository, so a normal new-chat handoff must
explicitly bridge those two layers.

When an outgoing conversation prepares a handoff because of chat length, an
executor switch, or another intentional conversation boundary:

1. complete every task mutation/validation that belongs to the outgoing
   conversation;
2. update the authoritative task capsule and regenerate its derived Markdown or
   handoff surface before releasing Heartbeat ownership;
3. using the exact active `turn_id`, emit one final
   `heartbeat_update(..., state="done")` stating that the durable handoff is
   ready;
4. do not perform additional task mutations or open another Heartbeat turn in
   the outgoing conversation after that release;
5. provide the already-prepared handoff prompt to the operator;
6. the receiving conversation uses the same real durable `task_id` and starts
   its first substantial response with `heartbeat_begin_turn`.

This release is mandatory for a planned handoff even though the durable task
remains `VALIDATING`, `IN_PROGRESS`, `CHECKPOINTED`, or another nonterminal
state. Heartbeat `done` means **this writer/turn is done**, not **the workspace
task is done**.

Do not add an automatic lease timeout or allow a new conversation to take over
an active task merely because a handoff is expected. If the old conversation is
still reachable, it owns the release. If it becomes unreachable before release,
use the orphaned-owner recovery procedure below.

## Semantic-delta emission policy

Heartbeat emission is **semantic first**.

Before emitting a later `heartbeat_update`, compare the candidate update with
the most recent Heartbeat in the current assistant response.

Emit when the new update teaches the operator something materially new about:

- the current diagnosis or working hypothesis;
- evidence that confirms or falsifies an important hypothesis;
- a newly resolved or newly introduced uncertainty;
- a decision between materially different approaches;
- a meaningful implementation or validation result;
- an important blocker or fail-closed boundary;
- a change in what should happen next;
- the start of a long opaque phase where the operator would otherwise lose
  visibility.

A commit, PR transition, merge, checkpoint, completed tool call, or phase
boundary is **not by itself** a reason to emit another Heartbeat.

If the core diagnosis, implications, and next action are substantially the same
as the previous Heartbeat, remain quiet and continue working.

Do not consciously optimize for a target number of Heartbeats. Short,
straightforward work may need very few. A difficult turn may need more if the
model's working understanding genuinely changes several times.

## Executor-touch emission policy

Semantic updates and executor liveness are separate contracts.

`heartbeat_begin_turn` and every `heartbeat_update` are executor touches as well as
semantic events. When meaningful semantic progress has not changed but the
assistant is still actively executing tool work, use
`heartbeat_touch(task_id, turn_id)` as a **silent liveness signal**.

The current v0.4.7 live card renders executor activity as **recent** only while
the last executor signal is at most 30 seconds old. The model cannot rely on an
autonomous wall-clock timer between tool calls, so active execution uses the
following deterministic emission rules:

- after a begin-turn, semantic update, or touch, perform **at most three
  non-Heartbeat tool operations** before another executor signal. If no semantic
  update is warranted, call `heartbeat_touch` before a fourth non-Heartbeat
  operation;
- call `heartbeat_touch` immediately before a known long or opaque tool
  operation, external wait, model run, download, CI wait/poll phase, or similar
  step that may otherwise let the 30-second freshness window expire;
- when such a long operation returns and more tool work will continue without a
  semantic update, touch before the next non-Heartbeat operation;
- during repeated polling of the same external dependency, keep semantic
  commentary compressed, but emit silent touches so active polling does not
  appear executor-stale;
- do **not** emit touches while the assistant is genuinely idle, waiting on the
  user, finished, blocked with no active execution, or otherwise unable to
  demonstrate fresh work. A touch is evidence of a model tool call at that
  instant, not proof of continuous process existence between calls.

A `heartbeat_touch` never creates semantic history, never substitutes for a
meaningful `heartbeat_update`, and **does not reset the 10-non-Heartbeat-tool
semantic-silence backstop** below. Track those two backstops independently.

If `heartbeat_touch` fails, do not claim fresh executor liveness. Preserve the
durable workspace task and continue through other healthy tools when safe; report
the Heartbeat transport/runtime problem at the next useful semantic update.

## Style

Write Heartbeat messages as natural point-in-time working summaries.

Prefer:

> The preserved job is still queued, so the restart happened before any runner
> claimed it. That narrows the fault to the recovery reconciliation path; I’m
> pulling the exact controller error next.

Avoid low-value narration such as:

> I fetched the run, checked the logs, inspected the branch, and am continuing.

Do not use heartbeat numbers, log-style headings, or generic "still working"
messages unless there is genuinely no stronger semantic summary available.

Do not expose private chain-of-thought or hidden scratch reasoning.

## Silence-prevention backstop

Semantic change is the primary trigger. Tool count is only a backstop against an
opaque execution wall.

- Aim to surface useful commentary around meaningful reasoning/execution
  transitions, often after roughly 1–3 meaningful execution steps when there is
  something new to say.
- Do not fabricate or paraphrase an update merely because several routine calls
  occurred.
- Before entering a known long opaque operation, emit a useful preamble if the
  operator would otherwise lose visibility.
- If **10 non-Heartbeat tool operations** occur without any Heartbeat, another
  non-Heartbeat tool operation is forbidden until a concise update summarizes
  the actual current understanding and next action.

There is no fixed elapsed-time requirement. The previous 15-second forced
cadence and three-tool hard lease are retired. Live prompt experiments showed
that they encourage redundant milestone narration.

A meaningful semantic state change expires the current silence lease
immediately: emit the update before proceeding into additional opaque work.

## Live-card retention

v0.4.5 accepts the **full bounded current-turn semantic chain** in one live card.

Turn isolation is mandatory: only updates matching the immutable
`task_id + turn_id` may appear. The full history is bounded by the server's
turn-history limit (default 50), while `recent` remains a latest-three
compatibility projection.

The card grows naturally with the first five current-turn Heartbeats. Beginning
with update six, the history region stays at the measured height of the first
five entries and scrolls internally. It should auto-follow new updates while the
operator is already near the bottom, but must not force-scroll away from an
earlier update the operator is actively reading.

v0.4.6 is a narrow sizing hotfix only. It preserves the v0.4.5 retention and
scroll behavior but changes `ui/notifications/size-changed` to report the
intrinsic rendered card height rather than the iframe/document viewport height.
This prevents short one- or two-update cards from leaving a large blank
transcript gap.

The sidebar/task history remains an optional history/debug surface rather than
the primary live UX. The semantic-delta emission policy is unchanged; showing
more retained updates must not encourage additional or lower-value Heartbeats.

## Plugin lifecycle after Heartbeat changes

A workspace-only semantic-policy change such as this procedure does **not**
require restarting the Heartbeat server, deleting/recreating the plugin, or
changing the MCP implementation.

For a breaking MCP/tool/UI release:

1. deploy and validate the new server/runtime;
2. before recreating/refreshing the plugin, close active Heartbeat turns with
   `state="done"` where practical so task ownership is released cleanly;
3. delete/recreate or refresh the custom Heartbeat plugin connection when
   needed to force a clean custom-MCP boundary;
4. perform a full browser refresh;
5. verify the actual tool surface before trusting an existing conversation;
6. resume each durable task using its real existing `task_id`. Never invent a
   replacement Heartbeat task ID merely to bypass ownership.

### Orphaned volatile-owner recovery

A stale owner can be created either by plugin recreation/browser refresh or by an outgoing chat becoming unreachable before a planned handoff release.

Plugin recreation/browser refresh can change the conversation/session identity
presented through `_meta["openai/session"]`. If a pre-refresh Heartbeat turn
was still active, the in-memory store may retain ownership under the old,
unreachable session identity.

The symptom is a valid existing task failing a new
`heartbeat_begin_turn` with
`HEARTBEAT_TASK_OWNED_BY_ANOTHER_CONVERSATION` immediately after a plugin
refresh/recreation, even though the same ChatGPT thread owned the task before
the refresh.

Treat either case as a **volatile Heartbeat ownership lock**, not as corruption of the
durable workspace-control task.

Recovery order:

1. if the old Heartbeat session is still reachable, close its active turn with
   `state="done"`;
2. otherwise, at a coordinated maintenance boundary, restart only the
   Workspace Heartbeat server/runtime to clear its in-memory ownership/history;
3. verify the Heartbeat endpoint is healthy;
4. retry `heartbeat_begin_turn` from the resumed chat using the original
   durable task ID;
5. do not create a fake/new Heartbeat task ID and do not mutate the owning
   workspace task merely to escape the stale lock.

The server restart clears **all volatile Heartbeat ownership/history in that
server process**, not only one task. It does not modify workspace-control task
capsules, Git state, Lambda CI state, research-engine state, or any other
durable task data. Coordinate the restart so another active chat is not relying
on the old in-memory Heartbeat state.

On the accepted Lambda deployment, the recovery operation is conceptually:

```bash
tmux kill-session -t workspace-heartbeat
heartbeat-up
```

Use the normal terminal-safe wrapper and health checks rather than issuing a
top-level shell `exit`.

Existing conversations are not inherently unusable after an upgrade. Field
evidence since v0.4.4 shows that long-running chats can acquire the new tool
contract after plugin recreation/browser refresh. Effective tool-surface
verification, not chat age alone, determines compatibility.

A compatible conversation must expose:

- `heartbeat_begin_turn`;
- `heartbeat_update` requiring `turn_id`;
- `heartbeat_get`;
- bounded `turn_history` on turn snapshots;

and must not expose legacy `heartbeat_open` or `heartbeat_render`.

If the tool surface is stale or ambiguous after refresh, use a fresh
conversation.

## Runtime state

Accepted baseline/runtime rollback:

```text
v0.4.5
/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v045/plugins/workspace-heartbeat
SHA c91ee09f6594e1e76134159b211fe224a8409b6b
rollback launcher: /home/atrott/bin/heartbeat-up.v045.rollback
```

Current live candidate under final host validation:

```text
v0.4.6
/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v046/plugins/workspace-heartbeat
SHA b5eb013c1d8d169cc1652d4f9013ad5ae17a7482
resource: ui://workspace-heartbeat/live-v5.html
```

Operator runtime entrypoint:

```bash
heartbeat-up
```

v0.4.6 has passed exact Node v20.20.2 tests (26/26), intrinsic-resize source
validation, isolated startup on port 8788, v0.4.5 pre-cutover/rollback checks,
managed cutover on port 8787, and local/public endpoint health. It is not yet
durably accepted until refreshed ChatGPT live-v5 visual acceptance confirms
both short-turn intrinsic sizing and the preserved six-plus-update scroller.

Older v0.4.4/v0.4.3 runtimes are historical rollback/implementation evidence,
not the current operating target.

## Shared representation

The optional structured snapshot remains defined by:

- `schemas/progress_heartbeat.v1.schema.json`;
- `scripts/progress_heartbeat.py`.

A heartbeat snapshot is ephemeral operator state by default. Do not commit one
to Git merely to report progress. Persist it only when an owning task explicitly
needs durable operator-state evidence.

The structured snapshot is an optional control representation, not a prose
template. Natural Heartbeat messages should follow the semantic-delta policy
above rather than mechanically restating every snapshot field.

## Polling is not progress

Repeated checks of the same external dependency must be compressed.

When CI or another external operation is the only remaining dependency, report
the decision boundary once. Do not emit a wall of near-identical messages such
as "checked workflow", "monitored jobs", "reviewed status", and "fetched logs".

A later update is justified only when the dependency changes, new evidence
changes the diagnosis, or the silence-prevention backstop is reached.

## Relationship to scope closure

Heartbeat does not authorize work.

If the owning objective is durably satisfied and validated, evaluate the Scope
Closure Gate. If closure returns `CHECKPOINT_AND_STOP`, stop rather than invent
another milestone.

A transition into unrelated implementation must be backed by new evidence or
explicit scope authorization.

## Relationship to external waits

External waits are control states, not excuses for scope expansion.

While CI, a benchmark, a model runtime, a human gate, or another dependency is
pending:

- useful independent in-scope work may continue if it cannot invalidate the
  pending operation;
- otherwise, do not create adjacent work merely to stay busy;
- report the pending dependency and the decision its result enables;
- poll at bounded decision points rather than tight loops.

## Initial and recovery commentary

At the first natural commentary point in a substantial assistant response,
`heartbeat_begin_turn` should summarize the most useful current state and next
action.

After interruption/recovery, that first message should identify the recovered
durable state, the first unfinished/invalid stage, and the immediate next
decision or milestone without replaying already-settled history.

## Rendering helper

The structured helper remains available:

```bash
python scripts/progress_heartbeat.py validate --file heartbeat.json
python scripts/progress_heartbeat.py render --file heartbeat.json
```

Cadence/gate behavior uses the semantic-delta-first policy with the 10-tool
silence backstop:

```bash
python scripts/progress_heartbeat.py due \
  --tool-calls 10 \
  --elapsed-seconds 0

python scripts/progress_heartbeat.py gate \
  --tool-calls 10 \
  --elapsed-seconds 0
```
