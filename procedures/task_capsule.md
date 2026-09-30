# Durable task-capsule procedure

## Purpose

Represent one concrete task execution in executor-neutral durable form so another
control cycle can recover the next correct and safe action without the previous
executor's private conversation state.

A task capsule coordinates execution. It does not replace project-owned
scientific, course, implementation, workflow, or artifact truth.

## Storage

Active capsules normally live at:

`tasks/active/<task_id>.json`

Completed capsules normally live at:

`tasks/archive/<task_id>.json`

The filename must match `task_id`.

## Versioned structural contracts

The schema entry point is:

`schemas/task_capsule.schema.json`

Versioned schemas are:

- `schemas/task_capsule.v1.schema.json`
- `schemas/task_capsule.v2.schema.json`

The deterministic validator dispatches on `schema_version`.
Unknown versions fail explicitly.

v1 remains supported so preserved Phase-3/Phase-4 evidence does not change
meaning merely because v2 exists.

## Validation

Run:

    python3 scripts/workspace_control.py task-validate \
      --file tasks/active/<task_id>.json

Machine-readable output:

    python3 scripts/workspace_control.py task-validate \
      --file tasks/active/<task_id>.json \
      --json

v1 validation preserves the existing checkout-centered task contract.

v2 validation adds structural/semantic checks for:

- execution topology;
- optional exact workflow identity/version;
- remote and/or local repository state;
- stage IDs and states;
- checkpoint/checkpoint-bundle entries;
- suspension/resume structure;
- artifact lifecycle metadata;
- registry mutation policy;
- COMPLETE and blocked/suspended status consistency.

The validator uses only the Python standard library.

## Human-readable handoff rendering

Render a derived Markdown view:

    python3 scripts/workspace_control.py task-render \
      --file tasks/active/<task_id>.json \
      --output tasks/active/<task_id>.md

Without `--output`, the rendered Markdown is written to stdout.

The JSON capsule plus verified Git/runtime evidence remain authoritative.

The rendered view:

- carries an explicit derived marker;
- identifies the authoritative capsule;
- includes current task/checkpoint information;
- includes blockers and next safe action;
- includes fresh-chat initialization text;
- is deterministic for a given capsule/control-root context.

The renderer refuses to overwrite an existing output that does not carry the
derived marker.

Regenerate the human-readable view after material capsule changes.

## Handoff assessment

Run:

    python3 scripts/workspace_control.py handoff-check \
      --file tasks/active/<task_id>.json

v1 handoff semantics remain unchanged in the current phase.

v2 capsules validate structurally, but topology-aware v2 handoff is intentionally
not implemented until its dedicated phase. Until then, `handoff-check` returns
`NOT_HANDOFF_SAFE` for a valid v2 capsule with an explicit reason instead of
applying v1 local-checkout assumptions to remote/composed tasks.

## Updating durable task state

Update the capsule when task state materially changes, especially after:

- an important decision;
- an operation that actually executed;
- artifact creation;
- validation;
- discovery/resolution of a blocker or gate;
- a checkpoint;
- a push/remote verification;
- a stage transition;
- a change in remaining work or next safe action.

Do not record an operation as executed until execution evidence exists.

Do not mark a remote checkpoint verified until the remote identity was actually
checked.

Where a derived Markdown handoff is maintained, refresh it after the capsule
update or mark it explicitly stale. The JSON remains authoritative.

## Workflow binding

When a v2 task uses a reusable workflow, record an exact durable workflow
identity such as repository + path + Git checkpoint/content identity.

Do not silently resume a long-running task against a materially changed workflow.

## Evidence discipline

Capsules distinguish:

- intended work from executed work;
- capability from authority;
- process completion from artifact validation;
- handoff-safe state from receiver-specific execution readiness;
- durable evidence from executor recollection.

Secrets, credentials, access tokens, and private keys do not belong in task
capsules or derived handoff views.

## Current phase boundary

`task-validate` and `task-render` support v2.

`handoff-check` remains v1-only until topology-aware handoff is implemented.

Preflight behavior is unchanged in this phase.
