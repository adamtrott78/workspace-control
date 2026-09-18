# Repository preflight procedure

## Purpose

Establish the actual repository/check-out state immediately before a read or
mutation operation.

This is the deterministic implementation of the portability contract's mutation
preflight requirement.

## Implementation

Canonical checkout:

```bash
python3 scripts/workspace_control.py preflight \
  --repo PADataset \
  --intent mutate
```

Specific worktree:

```bash
python3 scripts/workspace_control.py preflight \
  --repo PADataset \
  --path /absolute/path/to/worktree \
  --intent mutate
```

Machine-readable output is available with `--json`.

## Checks

The command establishes:

- logical repository identity;
- requested checkout/worktree path;
- actual Git top level;
- current branch;
- HEAD;
- observed origin;
- registry/origin agreement;
- remote canonical-branch SHA when mutation is proposed directly on the
  registered canonical branch;
- staged, unstaged, and untracked state;
- context-entry availability;
- registered parent-repository overlaps;
- writable/mutation policy.

## Mutation behavior

The preflight itself does not mutate the repository.

For a writable canonical branch, mutation preflight uses `git ls-remote` to
observe the currently advertised remote branch SHA without fetching or updating
local remote-tracking refs.

For `--intent mutate`:

- a non-writable repository is blocked;
- `recursive_mutation_forbidden` blocks mutation from that registered repository;
- repository/origin identity mismatch is blocked;
- a dirty checkout requires review by default;
- mutation directly on a canonical branch requires review if its local HEAD
  differs from the currently advertised remote canonical-branch SHA or if that
  remote state cannot be verified.

A caller may supply `--allow-dirty` only after the dirty state has been
explicitly reviewed and the intended mutation is known not to overwrite or
broadly stage unrelated work.

`--allow-dirty` does not authorize clean/reset/stash/delete behavior.

## Exit codes

- `0` — requested operation is ready under the checked policy/state;
- `10` — review is required before mutation;
- `20` — mutation is blocked by registry policy;
- `30` — repository identity/state could not be established safely;
- `2` — command-line usage error.

A nonzero preflight result is evidence that the next mutation should stop or be
replanned. It is not permission to bypass the check manually.
