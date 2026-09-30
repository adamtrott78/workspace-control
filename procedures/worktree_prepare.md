# Worktree preparation procedure

## Purpose

Prepare or inspect one bounded Git worktree without normalizing unrelated state.

`worktree-prepare` is deterministic and read-only by default. It may create a
missing isolated worktree only when the caller supplies explicit `--create`
authority and every precondition is already satisfied.

The command never treats technical ability as authority.

## Command

Read-only assessment:

```bash
python3 scripts/workspace_control.py worktree-prepare \
  --repo workspace-control \
  --branch control-plane-v2-refactor \
  --path /absolute/path/to/worktree \
  --expected-checkpoint <40-character-sha>
```

An alternate existing source checkout/worktree may be supplied with
`--source`. Otherwise the registered repository path from `repos.json` is
used.

Machine-readable output is available with `--json`.

## Explicit creation

A read-only assessment of a missing, safely creatable worktree returns
`CREATE_AVAILABLE`.

Creation requires a second invocation with explicit authority:

```bash
python3 scripts/workspace_control.py worktree-prepare \
  --repo workspace-control \
  --branch control-plane-v2-refactor \
  --path /absolute/path/to/worktree \
  --expected-checkpoint <40-character-sha> \
  --create
```

`--create` authorizes only the bounded `git worktree add` operation described
by the checked inputs. It does not authorize cleanup, synchronization, branch
rewrites, fetching, or unrelated filesystem changes.

If the requested local branch already exists at the exact expected checkpoint,
creation uses that branch.

If the local branch does not yet exist, creation may create that one branch at
the exact expected checkpoint only when:

- the branch exists on the registered remote;
- the advertised remote SHA exactly equals `--expected-checkpoint`;
- that commit already exists in the local Git object database;
- the branch is not already checked out elsewhere;
- the target path is missing and its parent directory already exists;
- repository mutation policy permits creation.

The command does not fetch missing objects or create missing parent directories.

## Existing target

When the target path already exists, the command is observational even if
`--create` is supplied.

`READY` requires:

- the target is a Git checkout/worktree of the registered logical repository;
- its current branch equals the requested branch;
- its HEAD equals the expected checkpoint;
- it is clean;
- the registered remote advertises the requested branch at the same checkpoint.

An existing dirty target returns `BLOCKED_DIRTY`.

Branch, HEAD, or advertised-remote disagreement returns
`BLOCKED_DIVERGED`.

A target that is not the registered repository identity returns
`BLOCKED_IDENTITY`.

## Missing target preconditions

Before reporting `CREATE_AVAILABLE` or creating anything, the command checks:

- repository write policy;
- `recursive_mutation_forbidden`;
- target parent existence;
- source checkout identity and registered origin;
- source cleanliness;
- target isolation from the source checkout;
- Git branch-name validity;
- advertised remote branch and exact checkpoint;
- local availability of the checkpoint commit;
- existing local branch identity, when present;
- whether the requested branch is already checked out in another worktree.

Any disagreement stops before creation.

## Result classes

- `READY` — the requested exact worktree exists and is safe to consume, or an
  explicitly authorized creation completed and was re-inspected successfully.
- `CREATE_AVAILABLE` — the target is missing and all creation preconditions
  pass, but `--create` was not supplied.
- `NEEDS_REVIEW` — state is incomplete or ambiguous, such as an unavailable
  remote check, missing local commit object, missing target parent, branch
  already checked out elsewhere, or a failed creation attempt.
- `BLOCKED_DIRTY` — relevant source/target worktree state is dirty.
- `BLOCKED_DIVERGED` — branch/HEAD/remote identities disagree with the exact
  expected checkpoint.
- `BLOCKED_IDENTITY` — a required checkout/path does not represent the
  registered logical repository.
- `BLOCKED_POLICY` — repository policy or isolation rules forbid the requested
  creation.

## Failure and ambiguity

If `git worktree add` returns nonzero, the command does not retry or roll back.
It inspects the target path if one appeared and returns `NEEDS_REVIEW` with the
actual post-state.

The next action is:

```text
inspect actual durable state
-> determine what completed
-> continue from the first safe incomplete stage
```

## Forbidden normalization

`worktree-prepare` never automatically:

- cleans;
- resets;
- stashes;
- fetches;
- pulls;
- force-checks-out;
- switches unrelated checkouts;
- moves an existing divergent branch;
- rewrites unrelated refs;
- deletes a worktree;
- removes files;
- creates parent directories;
- overwrites unrelated files.

Dirty or divergent state is evidence to stop, not permission to normalize it.

## Exit codes

- `0` — `READY`;
- `10` — `CREATE_AVAILABLE`, `NEEDS_REVIEW`, `BLOCKED_DIRTY`, or
  `BLOCKED_DIVERGED`;
- `20` — `BLOCKED_POLICY`;
- `30` — `BLOCKED_IDENTITY`;
- `2` — command-line usage error.
