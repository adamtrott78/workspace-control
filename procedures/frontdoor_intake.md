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
