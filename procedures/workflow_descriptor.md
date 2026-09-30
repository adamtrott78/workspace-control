# Reusable workflow descriptor procedure

## Purpose

A workflow descriptor records one reusable, authority-owned procedure:

```text
how this kind of task works
```

It is not a live task capsule and must not record where one particular execution
is now.

Workflow descriptors remain optional. A bounded ad-hoc task may use only a task
capsule when no reusable workflow contract is needed.

## Contract

Schema:

`schemas/workflow_descriptor.v1.schema.json`

Template:

`templates/workflow_descriptor.v1.json`

Validator:

```bash
python3 scripts/workspace_control.py workflow-validate \
  --file /path/to/workflow.json
```

Machine-readable output:

```bash
python3 scripts/workspace_control.py workflow-validate \
  --file /path/to/workflow.json \
  --json
```

The validator uses only the Python standard library and Git.

## Ownership

`owner.repository` names the registered repository that owns the workflow's
semantics.

The descriptor file must reside in a Git checkout/worktree whose `origin`
matches that registered repository. This preserves project-local authority:
project-specific workflow semantics stay in the owning project repository.

A workspace-level workflow may be owned by `workspace-control` only when the
workflow semantics themselves are workspace-level coordination rather than
project-domain truth.

`owner.context_path`, `entry_route`, authority-owner paths, artifact paths,
and forbidden-mutation paths/patterns must be repository-relative and must not
escape with `..`.

## Descriptor contents

v1 records stable procedure only:

- schema version;
- workflow ID;
- title and purpose;
- owning repository/context;
- exact entry route;
- ordered stages;
- stage execution owner;
- authority-owner paths;
- stage dependencies;
- required capability/surface classes;
- deterministic project entrypoint when one exists;
- expected artifacts;
- artifact-lifecycle declaration objects;
- validation requirements;
- gates;
- forbidden mutations;
- optional idempotency identity.

Stage dependencies must reference an earlier declared stage. This gives the
descriptor a deterministic topological order and rejects self, forward, and
unknown dependencies.

Artifact-lifecycle entries are only required to be objects in Phase 8. Their
detailed lifecycle semantics are deliberately deferred to the dedicated
artifact-lifecycle phase.

## Live task state is forbidden

A workflow descriptor must not contain live execution state such as:

- task status;
- current stage;
- checkpoints;
- blockers;
- remaining work;
- next safe action;
- last executor/surface;
- executed operations;
- execution decisions.

Those fields belong in the task capsule for one concrete execution.

The validator reports live-state fields explicitly rather than silently treating
the workflow descriptor as a task capsule.

## Exact durable binding

A structurally valid descriptor is operationally valid only when its exact Git
identity can be resolved.

The validator requires:

- the descriptor is inside a Git checkout/worktree;
- that checkout's `origin` matches `owner.repository`;
- the descriptor is tracked;
- the owning repository HEAD resolves to an exact commit;
- the descriptor blob exists at that HEAD;
- the current file content exactly matches the durable HEAD blob;
- the owner context path exists in the owning checkout.

On success, the validator returns:

```text
repository
repository-relative path
checkpoint_sha
content_sha
```

A v2 task capsule that depends on this workflow should pin that exact identity.
Do not silently migrate a task to a newer workflow version.

If the descriptor has uncommitted changes, is untracked, has the wrong Git
origin, or otherwise lacks a durable identity, validation fails rather than
manufacturing a binding.

## Template use

Copy `templates/workflow_descriptor.v1.json` into the repository that owns the
workflow, then replace the placeholder workflow ID, title, purpose, owner,
routes, stages, capabilities, validations, gates, and mutation boundaries.

After committing the descriptor in the owning repository, run
`workflow-validate` and use the returned binding when a task capsule references
that reusable workflow.

## Authority boundary

Validation proves descriptor structure, stage dependency semantics, repository
ownership, and exact durable identity.

It does not:

- grant mutation authority;
- prove a receiver is EXECUTION_READY;
- execute workflow stages;
- migrate a task to another workflow version;
- make workspace-control authoritative for project-domain semantics;
- define detailed artifact lifecycle behavior beyond the v1 structural
  declaration.
