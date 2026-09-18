# Codex adapter procedure

## Purpose

Add Codex as an executor without making Codex-specific mechanisms authoritative
for workspace or project workflows.

The executor-neutral control plane remains canonical.

## Adapter layers

The initial Codex adapter consists of:

- tracked global-instruction template:
  `adapters/codex/global/AGENTS.md`
- installed user-level instructions:
  `$CODEX_HOME/AGENTS.md` or `~/.codex/AGENTS.md`
- repository routing instructions:
  `AGENTS.md`
- repository Skill:
  `.agents/skills/workspace-control/SKILL.md`

## Authority

These files may improve discovery, safety, and automation.

They must not become independent sources of:

- workspace repository identity;
- mutation policy;
- project scientific truth;
- course truth;
- task execution evidence;
- artifact completion state.

Canonical authority remains in the README/context routes, `repos.json`,
tracked procedures, deterministic implementation, task capsules, runtime
evidence, and Git state.

## Global adapter synchronization

The tracked template is the reproducible source for the installed global
workspace safety adapter.

Initial installation copies:

    adapters/codex/global/AGENTS.md

to:

    ${CODEX_HOME:-$HOME/.codex}/AGENTS.md

If an existing global `AGENTS.md` or `AGENTS.override.md` is present, do not
overwrite it automatically. Review and reconcile it explicitly.

## Repository adapter

The root `AGENTS.md` must remain thin.

It should route Codex to canonical workspace-control sources rather than repeat
their substantive contents.

## Skill adapter

The `workspace-control` Skill is also thin.

It selects the relevant tracked procedures and canonical deterministic CLI. It
must not implement a competing copy of workspace policy.

## Validation

Validate the adapter in read-only Codex mode.

Codex should be able to identify:

- the global working agreements;
- the repository `AGENTS.md`;
- the workspace-control Skill;
- `README.md`;
- `policies/PORTABILITY_CONTRACT.md`;
- `repos.json`;
- the deterministic preflight command.

Adapter validation must not mutate the repository.

## Executor-portability requirement

Removing Codex, the global AGENTS file, repository AGENTS files, and Skills must
reduce automation/discovery only.

The established workspace workflow must remain operable through ChatGPT-assisted
human terminal execution.
