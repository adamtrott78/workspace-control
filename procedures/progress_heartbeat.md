# Operator Progress Heartbeat

Status: **Wave-3 v1 implemented**

## Purpose

Long-running work must remain understandable to the human operator while it is
happening.

Tool activity is not progress reporting. A sequence such as repeated GitHub
status reads, log fetches, or CI job inspections may be operationally necessary,
but it must not replace a concise explanation of:

- what bounded objective is being completed;
- what durable milestones are already complete;
- what operation is happening now and why it is necessary;
- what execute-now scope remains;
- what durable milestone comes next;
- what external dependency, if any, is preventing the next transition.

The heartbeat is an operator-facing reasoning summary. It is not private
chain-of-thought and must not expose hidden scratch reasoning.

## Shared representation

The optional structured snapshot is defined by:

- `schemas/progress_heartbeat.v1.schema.json`;
- `scripts/progress_heartbeat.py`.

A heartbeat snapshot is ephemeral operator state by default. Do not commit one
to Git merely to report progress. Persist it only when an owning task explicitly
needs durable operator-state evidence.

## Required heartbeat semantics

A useful heartbeat answers six questions:

1. **Objective** — what bounded result is the executor trying to produce now?
2. **Progress** — which meaningful milestones or execute-now items are complete?
3. **Now** — what operation is currently happening, and why is it on the critical
   path?
4. **Scope** — how many REQUIRED_CORRECTION, BOUNDED_ENABLING_CHANGE, and
   AUTHORIZED_SCOPE_EXPANSION items remain? How many findings are deferred?
5. **Next** — what durable milestone changes the task state next?
6. **Dependency** — if progress is externally blocked, what exact CI/runtime/
   human/remote dependency is pending?

The update should be concise. It may be prose rather than a rigid card so long as
these semantics remain clear.

## Cadence

Emit a human-readable heartbeat during substantial work when any of the
following occurs:

- the objective or diagnosis changes;
- a REQUIRED_CORRECTION, BOUNDED_ENABLING_CHANGE, or authorized expansion is
  discovered;
- a meaningful milestone starts or completes;
- external CI/runtime execution starts or finishes;
- recovery changes the first unfinished stage;
- the Scope Closure Gate is evaluated;
- approximately 15 seconds of operator-visible work pass without a meaningful
  update;
- roughly 2-3 tool operations occur without a meaningful update.

These cadence values are operator-feedback defaults, not scientific timing
requirements. Do not fabricate timestamps when the executor cannot observe them.

## Polling is not progress

Repeated checks of the same external dependency must be compressed.

When CI or another external operation is the only remaining dependency, say so
plainly, for example:

> The bounded implementation is complete; CI is the only remaining gate. I am
> not making additional changes while it runs. If it fails, I will diagnose only
> the failing path.

Do not emit a wall of near-identical messages such as "checked workflow",
"monitored jobs", "reviewed status", and "fetched logs" without explaining the
unchanged control state.

When an unchanged dependency persists, a later heartbeat should state that there
has been no meaningful state change and should not imply implementation progress.

## Explain why, not every tool call

A heartbeat should explain the decision boundary:

- why a validation run is required;
- why a correction is in scope;
- why no further mutation is justified;
- why recovery resumes from a particular stage;
- why an external dependency is the only remaining gate.

Do not narrate low-level connector mechanics unless they materially affect the
decision or reveal a failure.

## Relationship to scope closure

Heartbeat scope counts are derived from the current Scope Closure classification.

The heartbeat does not authorize work.

If a heartbeat reports zero required/enabling/authorized items and the owning
objective is durably satisfied and validated, evaluate the Scope Closure Gate.
If closure returns `CHECKPOINT_AND_STOP`, the executor must stop rather than
invent another milestone.

A sudden transition from zero execute-now items to unrelated implementation must
be backed by new evidence or explicit scope authorization.

## Relationship to external waits

External waits are control states, not excuses for scope expansion.

While CI, a benchmark, a model runtime, a human gate, or another external
dependency is pending:

- useful independent in-scope work may continue if it does not invalidate the
  pending operation;
- otherwise, do not create adjacent work simply to stay busy;
- report the pending dependency and the next decision that its result enables;
- poll at bounded decision points rather than tight loops.

## Initial and recovery heartbeat

At the start of a substantial task, provide a concise plan heartbeat describing
the bounded objective and first milestones.

After interruption/recovery, the first heartbeat should identify:

- the durable state recovered;
- completed milestones that will not be repeated;
- the first unfinished/invalid stage;
- the immediate next durable milestone.

## Rendering helper

Given a JSON snapshot:

```bash
python scripts/progress_heartbeat.py validate --file heartbeat.json
python scripts/progress_heartbeat.py render --file heartbeat.json
```

Cadence can be tested deterministically:

```bash
python scripts/progress_heartbeat.py due \
  --tool-calls 3 \
  --elapsed-seconds 8
```

This returns `EMIT` when the shared cadence says another operator update is
due.
