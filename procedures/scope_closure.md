# Scope Adherence and Scope Closure

Status: **Wave-3 v1 implemented**

## Purpose

This procedure prevents bounded work from expanding indefinitely through
adjacent, non-blocking improvements.

The governing rule is:

> Fix what is required to complete the owning task safely and durably. Record
> non-blocking adjacent improvements as follow-up work unless the owning scope
> explicitly authorizes expansion.

This procedure applies during normal repository work, not only runtime
certification or benchmark measurement.

## Scope envelope

Before substantial multi-step work, establish a compact scope envelope with:

- owning task ID;
- current objective;
- recorded next safe action;
- categories explicitly allowed now;
- categories deferred by default;
- explicit finding/workstream authorizations;
- closure policy.

Use schemas/scope_envelope.v1.schema.json and scripts/scope_control.py for the
shared mechanism.

The scope envelope does not replace the owning task capsule. It is a bounded
execution view derived from that authority.

## Finding classes

Every newly discovered implementation opportunity that could expand the work
should be classified before acting.

### REQUIRED_CORRECTION

Execute now when the finding affects correctness, safety, or durability of the
owning objective.

Examples:

- the current patch would corrupt authoritative state;
- the required operation can produce an unsafe result;
- the mutation is not durably checkpointed;
- a correctness defect invalidates the current result.

Required corrections are not scope creep.

### BOUNDED_ENABLING_CHANGE

Execute now when the finding directly blocks the recorded next_safe_action or
required validation.

Examples:

- CI cannot run because a required contract field is malformed;
- the owning runner cannot reach its authorized next stage without one small
  compatibility fix;
- a receipt field is required to recover the current operation safely.

The change should be the smallest bounded fix that unblocks the owning action.

### AUTHORIZED_SCOPE_EXPANSION

Execute only when the owning authority explicitly authorizes that finding or
workstream.

This classification exists for deliberate scope growth. It must not be inferred
from proximity, convenience, or "while I am here" reasoning.

### DEFERRED_FOLLOWUP

Do not implement now when the finding is useful but non-blocking.

Record:

- finding/issue;
- why it matters;
- evidence;
- suggested owner;
- urgency.

Then return to the owning task.

Examples:

- unrelated cleanup;
- generalized refactors;
- new abstractions not required by the current task;
- opportunistic hardening outside the failing path;
- extra experiments not required by the owning gate;
- improving adjacent runners simply because they were discovered.

## Scope Closure Gate

Evaluate the gate after the owning objective reaches a durable validated state,
and after every bounded corrective/enabling change.

If all of the following are true:

1. the owning objective is satisfied;
2. required validation has passed;
3. the current mutation/evidence is durably checkpointed;
4. no blocker prevents the recorded next safe action;
5. no remaining finding is classified as REQUIRED_CORRECTION,
   BOUNDED_ENABLING_CHANGE, or explicitly authorized scope expansion;

then the required decision is:

CHECKPOINT_AND_STOP

Deferred findings do not keep the current implementation session alive.

## Stop means stop

After CHECKPOINT_AND_STOP:

- checkpoint or synchronize the durable owning state if required;
- report deferred follow-ups;
- return the owning next_safe_action;
- do not continue browsing for adjacent improvements;
- do not add another hardening patch;
- do not start another experiment;
- do not redesign a neighboring subsystem.

A later task or explicit authorization may reopen a deferred item.

## Validation failures

A validation failure may justify additional work only when the failure is caused
by the current mutation or blocks the owning objective.

Classify the failure before patching it.

Do not use a failing check as permission to clean up unrelated pre-existing
debt.

## Discovery during long-running work

Long-running chats should periodically ask:

1. Did I just discover something necessary for correctness/safety/durability?
2. Does it block the recorded next safe action or required validation?
3. Was this work explicitly authorized?
4. If none apply, why am I implementing it instead of recording a follow-up?

If the answer to question 4 is only convenience, proximity, polish, or future
usefulness, defer it.

## Relationship to the Wave-3 actionability gate

The actionability gate bounds diagnosis:

- once the root cause and bounded safe correction are known, stop exploring.

The scope-closure gate bounds implementation:

- once the owning objective is durably satisfied and validated, stop improving
  adjacent surfaces.

Both gates are required. One prevents endless investigation; the other prevents
endless implementation.

## Recovery

On interruption:

- recover the owning task and scope envelope from durable state;
- recover any classified findings/follow-ups;
- resume only required/bounded/authorized work;
- do not promote deferred follow-ups into current work merely because the
  conversation restarted.

This keeps recovery from becoming a second scope-expansion event.
