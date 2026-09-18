# Workspace status procedure

## Purpose

Observe the current state of every logical repository registered in
`repos.json` without mutating project repositories.

This procedure is executor-neutral. Codex, ChatGPT-assisted terminal operation,
or a human operator may invoke the same implementation.

## Authority

Workspace identity and mutation policy come from:

`repos.json`

Current branch, HEAD, dirty state, origin, worktrees, and context availability
come from the actual local Git/filesystem state.

The registry must not be rewritten merely because observed runtime state changes.

## Implementation

```bash
python3 scripts/workspace_control.py status
```

Machine-readable form:

```bash
python3 scripts/workspace_control.py status --json
```

## Observations

For each logical repository the command reports, when available:

- registered path and role;
- writable policy;
- actual Git root;
- current branch and HEAD;
- observed `origin`;
- whether observed `origin` matches the registry;
- tracked staged/unstaged and untracked status counts;
- configured context-entry availability;
- registered parent-repository overlap;
- Git worktrees.

## Side effects

None intended.

The command does not:

- fetch;
- pull;
- checkout or switch;
- clean;
- reset;
- stash;
- stage;
- commit;
- push;
- alter project files.

## Interpretation

`clean: true` is an observation, not permission to mutate.

`writable: true` is policy permission, not proof that the current checkout is
appropriate for mutation.

Use the repository preflight procedure immediately before a mutation.
