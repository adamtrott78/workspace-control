# Adam Workspace Control Plane

This private repository owns cross-project operating policy for the working
environment under:

`~/adamArchives/Adam`

It is a **control plane**, not a super-repository and not a replacement for the
context owned by individual projects.

Project repositories retain authority for their own scientific, course,
application, and artifact-specific truth.

## Purpose

The control plane exists to make workflows portable across executors.

The primary supported execution modes are:

1. an agentic executor such as Codex;
2. ChatGPT directing a human-operated terminal through bounded copy/paste
   operations.

Changing executors should change the degree of automation, not the underlying
workflow architecture.

## Start here

For workspace-level work:

1. read this file;
2. read `policies/PORTABILITY_CONTRACT.md`;
3. inspect `repos.json`;
4. observe current repository/runtime state before mutation.

Do not recursively ingest all project repositories merely because they are
registered here.

## Ownership boundary

This repository owns:

- workspace topology;
- cross-repository operating policy;
- executor-portability requirements;
- future shared deterministic procedures;
- future agent adapters and Skills;
- future cross-project task coordination.

This repository does **not** own:

- PADataset scientific truth;
- MTH 602 course truth;
- project-specific experiment provenance;
- project-specific build or artifact semantics;
- copies of project repositories.

Those remain with their owning repositories.

## Architecture

The intended stack is:

```text
project/domain authority
        ↓
executor-neutral procedures
        ↓
workspace control plane
        ↓
agent adapters
        ↓
Codex OR ChatGPT + human terminal
```

Essential knowledge must remain usable if the agent-adapter layer disappears.

## Repository registry

`repos.json` records stable repository identity, ownership, and mutation policy.

It intentionally does not record volatile facts such as current branch, HEAD,
dirty state, running processes, or ahead/behind counts. Those must be observed
from the actual checkout when needed.

A logical repository may have multiple Git worktrees. Worktree instances are
runtime state, not separate repository identities.

JSON is used deliberately for the registry so the initial control-plane tooling
can parse it with the Python standard library and remain independent of
project-specific Python environments or third-party YAML packages.

## Deterministic control tooling

`scripts/workspace_control.py` is the initial executor-neutral control-plane CLI.

Its first commands are:

```text
workspace_control.py status
workspace_control.py preflight
```

The corresponding operating contracts live under `procedures/`.

These tools observe state. They do not fetch, clean, switch, stash, reset, stage,
commit, push, or otherwise normalize project repositories.

## Current maturity

Status: `EXPERIMENTAL`

The control-plane architecture and portability contract are being established
before Codex is installed or agent-specific instructions are added.
