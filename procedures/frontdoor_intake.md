# Instant front-door durable intake

## Purpose

The persistent ChatGPT Instant front door is the human-facing Workspace Control
surface for submitting high-level tasks, asking for durable status, and
providing explicit human decisions.

Conversation state is not task authority. A task-like message first becomes a
candidate-only durable intake record.

## Candidate storage

Pending task submissions are stored under:

`tasks/intake/<intake-id>.json`

The record binds the front-door conversation/message source and preserves the
human objective, but its `authorization_state` is always `UNDECIDED`.

The intake queue is not an execution queue and does not grant repository,
runtime, shell, model, or external-effect authority.

## Promotion boundary

A separate deterministic/policy-owned promotion step must:

1. load and validate the candidate;
2. recover relevant existing durable task/project state;
3. classify create-vs-resume-vs-status/decision intent;
4. construct or update a normal task capsule;
5. obtain whatever existing authority/policy is required for subsequent effects;
6. preserve the original intake source reference.

The front-door model cannot bypass this boundary.

## Status, decisions, and cancellation

Status/decision/cancel messages do not create new tasks by default. They must
resolve an existing durable task identity/state. Conversation memory may help
discovery but cannot substitute for durable lookup.

## Token economy

Front-door presentation may be concise and user-facing. Internal worker packets
default to machine-minimal output and minimum sufficient context. Waiting on
external work is a zero-model control-plane state.

## Existing-task control

The front door may resolve an explicit durable `task_id` for these operations:

- `QUERY_STATUS`: read-only projection from the authoritative task capsule;
  no candidate record and no model invocation are required by the control path.
- `RESUME_TASK`: persist a candidate requesting resume of the exact task.
- `PROVIDE_DECISION`: persist a candidate carrying the human decision for the
  exact task.
- `CANCEL_REQUEST`: persist a candidate requesting cancellation of the exact
  task.

Resume, decision and cancellation records use
`FRONTDOOR_TASK_CONTROL_CANDIDATE` and remain
`authorization_state=UNDECIDED`. They do not directly edit the task capsule,
scheduler state, authority state, repository state or external systems.

Existing-task operations fail closed without an explicit durable task identity.
Conversation-memory guesses are not enough. The Instant front door may use
connected GitHub/Workspace tools to discover candidate task identities, but
must resolve the final operation against the exact durable capsule.

## Status projection

Status output is deliberately compact and deterministic: task id, title,
durable status, current stage when present, next safe action, blockers,
remaining-work count and latest checkpoint id. The user-facing Instant model may
explain this projection concisely, but should not re-read or narrate unrelated
history merely to answer a status question.
