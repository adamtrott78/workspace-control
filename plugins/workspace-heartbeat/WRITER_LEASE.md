# Heartbeat single-writer lease hardening

Status: source candidate only; **not deployed**.

This change preserves the accepted v0.4.3 live-card/read model while adding a
single-writer lease per `task_id` using the hidden `openai/session` identity that
is already supplied by ChatGPT tool-call metadata.

## Invariant

Exactly one hidden ChatGPT session may write a given `task_id` at a time.
Different sessions may write different task IDs concurrently. Read-only
`heartbeat_open`, `heartbeat_snapshot`, and `heartbeat_get` never claim or
transfer writer ownership.

The hidden session identifier is internal lease material only. It is never
returned in tool output, model-facing logs, or UI state.

## First write and conflicts

The first successful `heartbeat_update` for a task claims its writer lease.
Further updates from the same session continue normally. A different session's
update fails closed before sequence/history/timeline/latest-task mutation.

## Normal chat handoff

Normal handoff is explicit and two-phase through `heartbeat_writer`:

1. the current writer calls `action=handoff` with the exact current task sequence;
2. the receiving chat calls `action=claim` with that same sequence;
3. only then may the receiving chat call `heartbeat_update`.

While a handoff is released but unclaimed, ordinary updates are rejected. An
`heartbeat_open` or read from another chat never completes the handoff.

## Recovery takeover

Recovery uses only `heartbeat_writer action=recover` and must provide the exact
current task sequence. A stale or incorrect sequence is rejected without
changing the writer lease. Successful recovery rebinds the task to the calling
session without appending history or incrementing sequence; the previous writer
is rejected on its next update.

## Validation

The regression suite covers conflict no-mutation, cross-task concurrency,
continued owner writes, read/open neutrality, normal handoff, recovery takeover,
stale recovery rejection, hidden-session redaction, live-card rolling history,
wrong-task isolation, hidden-card pause, terminal stop, and task-local side-panel
history.

Production runtime restart/deployment remains a separate reviewed gate.
