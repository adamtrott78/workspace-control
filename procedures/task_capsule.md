# Durable task-capsule procedure

## Purpose

Represent a multi-step task in an executor-neutral durable form so another
executor can determine the next correct and safe action without needing the
previous executor's private conversation state.

The task capsule coordinates execution. It does not replace repository-owned
scientific, course, implementation, or artifact truth.

## Storage

Active capsules normally live at:

`tasks/active/<task_id>.json`

Completed capsules normally live at:

`tasks/archive/<task_id>.json`

The filename must match `task_id`.

The structural contract is:

`schemas/task_capsule.schema.json`

## Structural and semantic validation

Run:

    python3 scripts/workspace_control.py task-validate \
      --file tasks/active/<task_id>.json

Machine-readable output:

    python3 scripts/workspace_control.py task-validate \
      --file tasks/active/<task_id>.json \
      --json

Validation checks include:

- required fields and value types;
- task ID syntax and filename agreement;
- supported task status;
- repository-entry structure;
- SHA syntax;
- evidence-entry structure;
- repository names against `repos.json`;
- mutation policy against `repos.json`;
- nonempty mutation scope for repositories that may be changed;
- status-specific consistency such as COMPLETE having no remaining work.

The validator uses only the Python standard library. It implements the v1 task
capsule contract directly rather than requiring a third-party JSON Schema
library.

## Handoff assessment

Run:

    python3 scripts/workspace_control.py handoff-check \
      --file tasks/active/<task_id>.json

Machine-readable output:

    python3 scripts/workspace_control.py handoff-check \
      --file tasks/active/<task_id>.json \
      --json

The handoff checker first validates the capsule and then compares it with actual
Git/filesystem state.

The initial v1 checker requires:

- an explicit handoff-capable task status;
- correct logical repository identity;
- matching checkout/worktree path;
- matching branch;
- current HEAD equal to recorded checkpoint SHA;
- checkpoint commit present locally;
- base SHA ancestral to checkpoint SHA;
- clean checkout;
- for mutation repositories, a pushed checkpoint whose remote branch currently
  advertises the exact checkpoint SHA.

A successful result is:

`HANDOFF_SAFE`

A structurally valid capsule that is not currently safe to transfer returns:

`NOT_HANDOFF_SAFE`

An invalid capsule returns:

`INVALID_CAPSULE`

## Exit codes

For `task-validate`:

- `0` — capsule is structurally and semantically valid;
- `30` — capsule is invalid or cannot be read safely;
- `2` — command-line usage error.

For `handoff-check`:

- `0` — `HANDOFF_SAFE`;
- `10` — `NOT_HANDOFF_SAFE`;
- `30` — `INVALID_CAPSULE` or state could not be established safely;
- `2` — command-line usage error.

## Updating a capsule

An executor should update the capsule when durable task state materially changes,
especially after:

- an important decision;
- an executed operation;
- creation of an artifact;
- validation;
- discovery of a blocker;
- a Git checkpoint;
- a push;
- a change in remaining work;
- a change in the next safe action.

Do not record a command as executed until execution evidence exists.

Do not set `checkpoint_pushed: true` until the remote branch has actually been
verified at that checkpoint.

## Executor switching

The receiving executor should need only:

1. the normal workspace-control entry route;
2. the task capsule;
3. the owning repository contexts and evidence referenced by that capsule.

A special prose explanation from the previous executor should not be necessary.

If the receiving executor cannot recover the next safe action from those durable
sources, the task is not handoff-safe even if a conversation contains the
missing information.
