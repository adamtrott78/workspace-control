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
2. a connected assistant using authorized direct mutation tools;
3. ChatGPT directing a human-operated terminal through bounded copy/paste
   operations;
4. hybrids of those modes when local runtime and remote tooling must cooperate.

Changing executors should change the degree of automation, not the underlying
workflow architecture, evidence standard, or authority model.

## Start here

For workspace-level work:

1. read this file;
2. read `policies/PORTABILITY_CONTRACT.md`;
3. read `policies/OPERATOR_WORKFLOW.md` when execution, mutation, Git, runtime,
   artifact validation, or task-transition routing is involved;
4. read `policies/TUTORING_CONTRACT.md` when building or operating a
   repository-backed course tutor;
5. inspect `repos.json`;
6. observe current repository/runtime state before mutation.

Routing is continuous rather than startup-only. When a conversation materially
changes task ownership, return to the owning project route and load the new owner
before acting.

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
Codex / connected direct tools / ChatGPT + human terminal
```

Essential knowledge must remain usable if the agent-adapter layer disappears.

## Shared policy contracts

The control plane now has two provisional reusable policy contracts in addition
to the portability contract:

- `policies/OPERATOR_WORKFLOW.md` owns executor-neutral mutation, runtime,
  validation, Git synchronization, and mid-conversation rerouting semantics;
- `policies/TUTORING_CONTRACT.md` owns reusable repository-backed tutoring
  semantics, including learning/completion modes, mastery evidence, pedagogical
  persistence, report provenance, and deadline recovery.

Project repositories should route to these shared owners and retain only their
own domain-specific supplements. They should not copy the complete shared
contracts into each project.

These policies are currently compatibility bridges. PADataset remains unchanged
until cold-start and cross-executor validation justify a later migration.

For new course-tutor projects:

- start from `templates/COURSE_TUTOR_ADAPTER.md` and fill only the local
  course-specific mappings and exceptions;
- validate the result with `procedures/TUTOR_EVALUATION.md`;
- keep the shared contracts in this repository rather than copying them into each
  course repository.

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

Mutation preflight performs a read-only `git ls-remote` query when mutation is
proposed directly on a registered canonical branch. This checks the advertised
remote branch SHA without updating local Git refs.

## Durable task capsules

Long-running or executor-switchable work is represented by machine-readable
task capsules under `tasks/`.

The structural contract is `schemas/task_capsule.schema.json`, and the operating
contract is `procedures/task_capsule.md`.

The executor-neutral CLI now also provides:

- `workspace_control.py task-validate`
- `workspace_control.py handoff-check`

`task-validate` checks capsule structure and registry policy.

`handoff-check` combines the capsule with current Git/filesystem state and
reports whether the task is actually `HANDOFF_SAFE`.

A task capsule coordinates work; it does not become a source of project-domain
truth.

## Current maturity

Status: `EXPERIMENTAL`

The control-plane architecture and portability contract are being established
before Codex is installed or agent-specific instructions are added.
