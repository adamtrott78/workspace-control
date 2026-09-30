# Global Codex working agreements

These instructions are universal discovery and safety defaults only.
Repository-owned instructions and context remain authoritative for
repository-specific work.

## Repository discovery

When a repository supplies a root routing file such as `AGENTS.md` or
`README.md`, use it to locate the repository's tracked authority.

For workspace-control specifically, route through:

```text
README.md
-> policies/PORTABILITY_CONTRACT.md
-> policies/OPERATOR_WORKFLOW.md when execution is involved
-> relevant tracked procedure
```

Do not reproduce repository policy inside this global file.

## Durable authority

Durable repository context, tracked procedures, task/workflow state, runtime
evidence, and actual Git state outrank executor memory.

Project-specific scientific, course, application, artifact, and workflow truth
belongs to the owning project repository, not global Codex instructions.

## Scope discipline

Read only the repository context required for the current task.

Do not recursively inventory unrelated repositories merely because they are
visible or registered.

A global adapter does not grant mutation authority. Use the owning repository's
normal routing and deterministic preflight mechanisms before mutation.

## Portability

Removing this global file must reduce discovery convenience only.

It must not remove any canonical workspace-control workflow, policy, validation
rule, or project-domain authority.
