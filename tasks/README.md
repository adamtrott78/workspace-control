# Durable task capsules

Task capsules are executor-neutral durable snapshots used when work may span:

- multiple sessions;
- multiple repositories;
- substantial runtime;
- executor changes;
- multiple operation surfaces;
- human/external-tool suspension and resume.

Active capsules normally live at:

`tasks/active/<task_id>.json`

Completed capsules normally live at:

`tasks/archive/<task_id>.json`

## Authority

A task capsule coordinates work. It does not replace project-domain truth or a
project-owned reusable workflow.

## Schema versions

The structural entry point is:

`schemas/task_capsule.schema.json`

Supported versioned schemas:

- v1: `schemas/task_capsule.v1.schema.json`
- v2: `schemas/task_capsule.v2.schema.json`

`task-validate` dispatches according to the capsule's `schema_version`.

## Human-readable view

`task-render` can produce `tasks/active/<task_id>.md` as a derived convenience
view.

The JSON capsule plus verified Git/runtime evidence remain authoritative.

The Markdown view must never become a competing source of task truth.

## v1

v1 preserves the original local-worktree-centered task/handoff contract used by
the Phase-3/Phase-4 evidence.

## v2

v2 adds representation for:

- remote-only, local, and composed task topology;
- exact workflow-version binding;
- stage progress;
- checkpoint bundles;
- suspension/resume;
- artifact lifecycle metadata;
- remote/local identities needed for recovery.

Topology-aware v2 `HANDOFF_SAFE` checking evaluates durable recovery state
for remote-only, local, and composed topologies without applying v1
local-checkout assumptions to remote-only tasks.

Receiver-specific `EXECUTION_READY` is reported separately from durable handoff
safety. Optional receiver checks describe transient capability/access facts and
do not grant authority or become durable task truth.

## Evidence discipline

A capsule does not make an unsupported claim true merely because the claim is
written into JSON.

Prefer independently recheckable identities and validation evidence.
