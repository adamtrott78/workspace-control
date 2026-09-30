---
name: workspace-control
description: Thin Codex discovery adapter for workspace-control status, preflight, worktree preparation, durable task state, handoff, and reusable workflow validation. Canonical authority remains in tracked workspace/project sources.
---

Use the existing executor-neutral workspace-control architecture.

1. Read `README.md`.
2. Read `policies/PORTABILITY_CONTRACT.md`.
3. Read `policies/OPERATOR_WORKFLOW.md` when execution, mutation, Git,
   runtime, validation, or routing is involved.
4. Inspect `repos.json`.
5. Read only the procedure required for the task:
   - `procedures/workspace_status.md`
   - `procedures/repo_preflight.md`
   - `procedures/worktree_prepare.md`
   - `procedures/task_capsule.md`
   - `procedures/workflow_descriptor.md`
6. If a task capsule exists, treat its exact durable state as coordination
   authority rather than relying on conversation memory.
7. If a reusable workflow is bound, resolve the exact pinned workflow identity.
8. Invoke `scripts/workspace_control.py` for deterministic control operations.

Canonical command families:

```text
python3 scripts/workspace_control.py status
python3 scripts/workspace_control.py preflight
python3 scripts/workspace_control.py worktree-prepare
python3 scripts/workspace_control.py task-validate
python3 scripts/workspace_control.py task-render
python3 scripts/workspace_control.py handoff-check
python3 scripts/workspace_control.py workflow-validate
```

This Skill does not own policy, project-domain truth, mutation authority,
workflow semantics, task progress, or execution evidence. It only routes Codex
to the tracked executor-neutral sources that do.

Use `--json` when machine-readable output materially improves the workflow.
