# Repository preflight procedure

## Purpose

Establish the repository state relevant to the execution topology immediately
before a read or mutation operation.

This is the deterministic implementation of the portability contract's
topology-aware preflight requirement. Preflight observes state; it does not
normalize repositories or grant mutation authority.

## Local topology

The existing invocation remains valid and keeps its v1 local-checkout behavior:

```bash
python3 scripts/workspace_control.py preflight \
  --repo PADataset \
  --intent mutate
```

The equivalent explicit form is:

```bash
python3 scripts/workspace_control.py preflight \
  --repo PADataset \
  --topology local \
  --intent mutate
```

A specific worktree may still be selected with `--path`.

Local preflight establishes, as applicable:

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

For a writable canonical branch, mutation preflight uses `git ls-remote` to
observe the currently advertised remote branch SHA without fetching or updating
local remote-tracking refs.

## Remote topology

Remote-only work MUST NOT require or manufacture a local checkout merely to
satisfy preflight.

Use `--topology remote` and identify the branch being inspected. A
ref-dependent mutation also supplies the exact expected parent:

```bash
python3 scripts/workspace_control.py preflight \
  --repo workspace-control \
  --topology remote \
  --branch control-plane-v2-refactor \
  --intent mutate \
  --expected-parent 77c7355bbafeb674dd35b55bcfdb542d50c6079c \
  --surface-write-ready \
  --consequence reversible \
  --allowed-path scripts/workspace_control.py \
  --allowed-path procedures/repo_preflight.md \
  --allowed-path tests/test_workspace_control.py \
  --allowed-path 'tests/fixtures/**' \
  --mutation-path scripts/workspace_control.py \
  --mutation-path procedures/repo_preflight.md \
  --mutation-path tests/test_workspace_control.py
```

Remote preflight queries the registered remote URL directly with
`git ls-remote`. It does not inspect the registered local path, create a
checkout, fetch, switch branches, or update local refs.

It establishes, as applicable:

- logical repository identity from `repos.json`;
- exact registered remote;
- requested remote branch;
- advertised branch SHA;
- expected parent/checkpoint for ref-dependent mutation;
- writable and recursive-mutation policy;
- declared mutation scope and proposed mutation paths;
- declared consequence class;
- confirmation that the selected operation surface has the required mechanical
  write capability/access.

`--surface-write-ready` is only a capability/access assertion. It does not
grant task authority. Likewise, `--allowed-path` values must come from the
owning durable task/workflow authority; supplying a pattern to the CLI does not
make that pattern authoritative.

For remote mutation:

- an expected parent is required;
- a mismatch between expected parent and the advertised branch SHA requires
  review;
- missing write capability/access confirmation requires review;
- the consequence class must be explicit;
- `destructive` and `external` consequence classes require additional
  authority or human-gate validation outside this preflight;
- a proposed mutation path outside the supplied allowed scope is blocked by
  policy.

## Composed execution

There is deliberately no opaque `--topology composed` preflight.

A composed workflow performs the required remote and local preflights
independently, then records or verifies the synchronization boundary before
crossing surfaces. At that boundary establish:

- expected remote checkpoint;
- expected local checkpoint;
- required synchronization direction;
- local dirty state;
- the transition rule.

A remote mutation MUST NOT be treated as if it moved an existing local checkout.
The local side must be explicitly synchronized and then locally preflighted
before a local/runtime stage consumes the remote result.

## Mutation behavior

Preflight itself never cleans, resets, stashes, switches, force-checks-out,
deletes, stages, commits, pushes, or otherwise normalizes a repository.

For local `--intent mutate`:

- a non-writable repository is blocked;
- `recursive_mutation_forbidden` blocks mutation from that registered
  repository;
- repository/origin identity mismatch is blocked;
- a dirty checkout requires review by default;
- mutation directly on a canonical branch requires review if its local HEAD
  differs from the advertised remote canonical-branch SHA or if that remote
  state cannot be verified.

A caller may supply `--allow-dirty` only after local dirty state has been
explicitly reviewed and the intended mutation is known not to overwrite or
broadly stage unrelated work.

`--allow-dirty` is local-only and does not authorize
clean/reset/stash/delete behavior.

## Machine-readable output

Use `--json`.

Backward-compatible local preflight retains the v1 payload shape. Remote
preflight emits a topology-explicit v2 payload containing the advertised SHA,
expected parent, consequence, capability assertion, allowed scope, proposed
mutation paths, result, and reasons.

## Exit codes

- `0` — requested operation is ready under the checked policy/state;
- `10` — review is required before mutation;
- `20` — mutation is blocked by registry or bounded-scope policy;
- `30` — repository identity/state could not be established safely;
- `2` — command-line usage error.

A nonzero preflight result is evidence that the next mutation should stop or be
replanned. It is not permission to bypass the check manually.
