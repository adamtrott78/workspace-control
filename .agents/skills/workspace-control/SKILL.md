---
name: workspace-control
description: Use for workspace-level repository status, mutation preflight, durable task-capsule validation, or executor handoff assessment in the Adam workspace. Do not use this Skill as a replacement for project-specific repository context or domain authority.
---

Use the existing executor-neutral workspace-control architecture.

1. Read the repository root `README.md`.
2. Read `policies/PORTABILITY_CONTRACT.md`.
3. Inspect `repos.json`.
4. Read the specific operating procedure required for the task:
   - `procedures/workspace_status.md` for workspace observation;
   - `procedures/repo_preflight.md` before repository mutation;
   - `procedures/task_capsule.md` for durable task state and handoff.
5. Invoke the canonical implementation in `scripts/workspace_control.py`.
6. Do not reproduce or reimplement policy logic inside this Skill.
7. Do not claim a mutation, runtime action, push, artifact, or validation
   occurred unless execution evidence establishes it.
8. Do not bypass a nonzero deterministic preflight or handoff result.
9. Do not mutate a repository marked non-writable in `repos.json`.
10. Keep project-specific scientific, course, application, and artifact truth
    in the owning project repository.

Canonical command families:

    python3 scripts/workspace_control.py status
    python3 scripts/workspace_control.py preflight
    python3 scripts/workspace_control.py task-validate
    python3 scripts/workspace_control.py handoff-check

Use `--json` when machine-readable output materially improves the workflow.
