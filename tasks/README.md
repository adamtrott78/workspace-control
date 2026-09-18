# Durable task capsules

Task capsules are executor-neutral durable records used when work may span:

- multiple sessions;
- multiple repositories;
- substantial runtime;
- substantial agent quota;
- an executor handoff.

Active task capsules should normally live at:

`tasks/active/<task_id>.json`

Completed task capsules should normally move to:

`tasks/archive/<task_id>.json`

The filename should match `task_id`.

## Authority

A task capsule coordinates work. It does not replace the scientific, course,
artifact, or implementation authority of the repositories it references.

Repository names in a capsule refer to logical repositories registered in
`repos.json`.

## Required durable state

A capsule records:

- task identity and goal;
- acceptance criteria;
- constraints;
- participating repositories;
- checkout/worktree paths;
- branches;
- base and checkpoint SHAs;
- whether mutation checkpoints were pushed;
- allowed mutation scope;
- decisions;
- operations that actually executed and their evidence;
- artifacts and their evidence;
- validation;
- blockers;
- remaining work;
- the next safe action.

`last_executor` is descriptive only. It is not part of task identity.

## Status model

Supported states are:

- `PLANNED` — task has been defined but execution has not begun;
- `IN_PROGRESS` — active mutation or analysis is underway;
- `VALIDATING` — produced work is being checked against acceptance criteria;
- `CHECKPOINTED` — a deliberate durable executor-switch point exists;
- `BLOCKED_RUNTIME` — continuation requires unavailable runtime resources;
- `BLOCKED_EVIDENCE` — continuation requires evidence that is not currently available;
- `NEEDS_USER_DECISION` — continuation requires an explicit user choice;
- `COMPLETE` — acceptance criteria have been satisfied and remaining work is empty.

`CHECKPOINTED` is the normal state for a deliberate executor handoff.

The blocked states may also be handoff-safe when the blocker, checkpoint, and
next safe action are durably recorded.

`PLANNED`, `IN_PROGRESS`, and `VALIDATING` are not treated as handoff-safe by the
initial deterministic checker because they imply that execution is not at an
explicit transfer boundary.

## Handoff-safe v1 boundary

The initial deterministic handoff checker is intentionally conservative.

For a capsule to be reported `HANDOFF_SAFE`:

- the capsule must pass structural and semantic validation;
- its status must be a permitted handoff state;
- every referenced logical repository must still match `repos.json`;
- every referenced checkout/worktree must exist and match the registered origin;
- its current branch must match the capsule branch;
- its current HEAD must equal the recorded checkpoint SHA;
- the checkpoint must exist as a commit;
- the recorded base SHA must be an ancestor of the checkpoint;
- the checkout must be clean;
- a repository with `intent: mutate` must have a nonempty allowed mutation scope;
- a mutation checkpoint must be recorded as pushed;
- the advertised remote task branch must exist and point to that exact checkpoint.

This v1 checker therefore requires a clean checkpoint. The portability contract
allows richer future designs in which precisely documented dirty state may also
be recoverable, but that capability is not claimed by the initial implementation.

## Evidence discipline

A capsule must distinguish:

- intended work from work that actually executed;
- process completion from artifact validation;
- executor recollection from durable evidence.

Evidence strings may reference:

- Git SHAs;
- paths;
- logs;
- result files;
- validation summaries;
- external state that can be independently rechecked.

A capsule does not make an unsupported claim true merely because the claim is
written into JSON.
