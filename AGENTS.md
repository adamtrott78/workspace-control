# workspace-control Codex routing

This file is an adapter, not an authority.

For workspace-control tasks:

1. Start with `README.md`.
2. Read `policies/PORTABILITY_CONTRACT.md`.
3. Inspect `repos.json`.
4. Read only the procedure relevant to the task under `procedures/`.
5. Use `scripts/workspace_control.py` for deterministic status, preflight,
   task validation, and handoff assessment.
6. Before repository mutation, run the canonical preflight procedure.
7. For long-running or executor-switchable work, use the canonical task-capsule
   procedure rather than keeping essential state only in the conversation.

Do not duplicate project-domain truth here.

Do not treat this file, a Skill, Codex memory, or an MCP result as a replacement
for owning repository context or execution evidence.

Do not mutate repositories marked non-writable in `repos.json`.

Do not recursively inspect registered repositories merely because they are
listed in the registry.
