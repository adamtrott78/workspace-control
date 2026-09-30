# workspace-control Codex routing

This file is a thin Codex adapter, not an authority.

For workspace-control tasks:

1. Start with `README.md`.
2. Read `policies/PORTABILITY_CONTRACT.md`.
3. Read `policies/OPERATOR_WORKFLOW.md` when execution, mutation, Git,
   runtime, validation, or task-transition routing is involved.
4. Inspect `repos.json`.
5. Read only the relevant procedure under `procedures/`.
6. When durable task state is involved, read `procedures/task_capsule.md`
   and the authoritative task capsule.
7. When a reusable workflow is bound, read
   `procedures/workflow_descriptor.md` and the exact pinned descriptor.
8. Invoke `scripts/workspace_control.py` rather than reimplementing
   deterministic control logic inside this adapter.

Useful command families include:

```text
workspace_control.py status
workspace_control.py preflight
workspace_control.py worktree-prepare
workspace_control.py task-validate
workspace_control.py task-render
workspace_control.py handoff-check
workspace_control.py workflow-validate
```

Do not duplicate project-domain truth, workspace policy, task state, workflow
semantics, or execution evidence here.

Do not treat this file, a Skill, Codex memory, or a connector/tool result as a
replacement for owning repository context, tracked procedures, durable task
state, or actual runtime/Git evidence.

Project-specific scientific, course, application, artifact, and workflow truth
remains in the owning project repository.

Routing is continuous: when task ownership changes, return to the owning route
before acting.
