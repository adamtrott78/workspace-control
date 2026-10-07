# Operator Progress Heartbeat

Status: **Workspace Heartbeat v0.4.4 accepted**

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

## Accepted ChatGPT Workspace Heartbeat delivery — v0.4.4

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
   `heartbeat_snapshot(task_id, turn_id)` and displays the latest three
   updates for that turn;
7. use `heartbeat_get(task_id)` only for explicit task-history/sidebar
   inspection. It is not the routine live-progress path;
8. when the owning task is actually complete, a terminal
   `heartbeat_update(..., state="done")` may close the active turn and release
   task ownership.

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
cadence and three-tool hard lease are retired for ChatGPT v0.4.4 because live
prompt experiments showed that they encourage redundant milestone narration.

A meaningful semantic state change expires the current silence lease
immediately: emit the update before proceeding into additional opaque work.

## Live-card retention

The accepted in-chat card shows the **latest three updates for the current
assistant turn**.

Do not increase that number preemptively. Live experiments produced compact,
nonredundant chains of two to four updates across turns ranging from under one
minute to more than ten minutes. Latest-three remains the default until a real
turn demonstrates that losing an earlier nonredundant update materially harms
operator understanding.

The sidebar/task history may retain older updates, but it is an optional
history/debug surface rather than the primary live UX.

## Plugin lifecycle after Heartbeat changes

A workspace-only semantic-policy change such as this procedure does **not**
require restarting the Heartbeat server, deleting/recreating the plugin, or
changing the MCP implementation.

For a breaking MCP/tool/UI release:

1. deploy and validate the new server/runtime;
2. delete/recreate the custom Heartbeat plugin connection when needed to force
   a clean custom-MCP boundary;
3. perform a full browser refresh;
4. verify the actual tool surface before trusting an existing conversation.

Existing conversations are not inherently unusable after an upgrade. Field
evidence on v0.4.4 showed that an existing long-running chat acquired the new
tool contract after plugin recreation/browser refresh and explicit tool-surface
use.

A conversation is v0.4.4-compatible only if its effective tool surface exposes:

- `heartbeat_begin_turn`;
- `heartbeat_update` requiring `turn_id`;
- `heartbeat_get`;

and does **not** expose legacy `heartbeat_open`.

If the tool surface is stale or ambiguous, use a fresh conversation.

## Accepted runtime

The accepted Lambda runtime is:

```text
/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v044/plugins/workspace-heartbeat
```

Operator runtime entrypoint:

```bash
heartbeat-up
```

The accepted v0.4.4 implementation SHA is:

```text
bbb4f09fac1864196b62a3126803a11b233d01f4
```

The v0.4.3 launcher/runtime is retained only as rollback history.

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
