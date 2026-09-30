# Codex adapter procedure

## Purpose

Integrate Codex as an executor/discovery surface without making Codex-specific
files authoritative for workspace or project workflows.

The executor-neutral control plane remains canonical.

## Adapter files

The tracked Codex adapter layer consists of:

- repository routing: `AGENTS.md`
- workspace-control Skill: `.agents/skills/workspace-control/SKILL.md`
- tracked global adapter template: `adapters/codex/global/AGENTS.md`
- this procedure: `procedures/codex_adapter.md`

These files are discovery/routing aids only.

## Canonical route

A Codex session working in workspace-control should recover the same authority
chain as any other executor:

```text
README.md
-> policies/PORTABILITY_CONTRACT.md
-> policies/OPERATOR_WORKFLOW.md when execution/mutation/runtime is involved
-> repos.json
-> relevant procedure
-> exact task capsule and/or workflow descriptor when applicable
-> scripts/workspace_control.py for deterministic control operations
```

Project-local work then continues through the owning project repository's own
route. The adapter layer must not substitute for project-domain authority.

## Thinness requirement

Adapter files may:

- improve discovery;
- point to tracked policy/procedure owners;
- list canonical command families;
- identify where durable task/workflow state is resolved.

Adapter files must not independently define:

- repository identity or write policy;
- project scientific/course/application truth;
- mutation authority;
- task progress;
- workflow semantics;
- handoff correctness;
- executor readiness;
- artifact completion;
- validation evidence.

No Codex-only workflow semantics are permitted.

## Global installation

The tracked global adapter may be installed as:

```text
${CODEX_HOME:-$HOME/.codex}/AGENTS.md
```

Installation is an external user/environment action, not part of repository
validation.

Do not automatically overwrite an existing user-level `AGENTS.md` or
`AGENTS.override.md`. Reconcile existing instructions explicitly.

The tracked global template remains non-authoritative even when installed.

## Repository adapter discovery

A read-only Codex discovery check should be able to identify, without mutation:

- the repository `AGENTS.md`;
- the workspace-control Skill;
- `README.md`;
- `policies/PORTABILITY_CONTRACT.md`;
- `policies/OPERATOR_WORKFLOW.md`;
- `repos.json`;
- the relevant tracked procedure;
- task-capsule and workflow-descriptor procedures when applicable;
- `scripts/workspace_control.py`.

For a mutation-oriented question, Codex should discover the canonical preflight
path rather than inventing a Codex-specific safety workflow.

## Portability gate

The adapter layer passes only if removing:

- root `AGENTS.md`;
- the workspace-control Skill;
- the global Codex adapter;
- this adapter procedure

reduces discovery/automation convenience but leaves the underlying workflow
conceptually operable through the normal README, policy, procedure, registry,
task/workflow, and deterministic-CLI routes.

That is, the dependency direction must remain:

```text
canonical workflow -> optionally discovered through Codex adapters
```

and never:

```text
Codex adapter -> required source of workflow semantics
```

## Validation discipline

Adapter validation is read-only.

Do not mutate project repositories, create worktrees, change branches, or
rewrite task state merely to test adapter discovery.

The preserved Phase-4 Codex adapter evidence is useful implementation evidence,
but current v2 routing and exact current Git state remain authoritative.
