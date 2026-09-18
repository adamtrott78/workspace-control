# Global Codex working agreements

These instructions are universal safety defaults only. Repository-owned
instructions and context remain authoritative for repository-specific work.

## Repository safety

- Before mutating a Git repository, establish the actual repository root,
  branch, HEAD, origin, and dirty/staged state.
- Never infer repository or worktree identity from the shell prompt, an open
  editor, a prior conversation, or remembered state.
- Do not automatically clean, reset, stash, switch branches, overwrite,
  delete, or broadly stage unrelated work.
- Do not use `git add .` in a dirty research, coursework, or multi-worktree
  repository.
- Prefer an isolated task worktree when existing work is unrelated or dirty.
- Treat proposed commands and inspected commands as unexecuted until actual
  execution evidence exists.

## Durable authority

- Durable repository context, tracked procedures, validated artifacts, runtime
  evidence, and actual Git state outrank executor memory.
- Do not move project-specific scientific, course, or artifact truth into
  global Codex instructions.
- If a repository provides its own AGENTS.md, README, context routes, or
  deterministic procedures, follow those rather than inventing a parallel
  workflow.

## Scope discipline

- Read only the repository context and source material required for the task.
- Do not recursively inventory unrelated repositories or worktrees.
- Treat externally owned or explicitly read-only repositories as read-only
  unless the user explicitly changes that policy.
