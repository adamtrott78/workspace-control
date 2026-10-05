# Lambda CI Root Provisioner Protocol v1

Status: static design; not installed.

The root provisioner is a **local privilege-boundary service**, not a generic
remote executor.

## Trust split

- `ci-controller` owns the pinned GitHub scale-set client and repository-scoped
  GitHub App/PAT material.
- `workspace-ci-provisioner` runs with root authority only because systemd
  sandbox/device/network policy and project UID setup require it.
- Project runner code executes only as the manifest's project UID.

The provisioner has **no GitHub credential** and requires no public-network
access.

## Transport

Pilot transport: root-owned Unix-domain socket.

Recommended path:

`/run/workspace-ci/provisioner.sock`

Socket permissions:

- owner: `root`
- group: `workspace-ci-controller`
- mode: `0660`

Only `ci-controller` is a member of `workspace-ci-controller`.

## Request

Exactly one JSON object per request:

```json
{
  "schema_version": 1,
  "request_id": "<uuid>",
  "project_id": "research-engine",
  "profile": "cpu-test",
  "runner_name": "lambda-research-engine-<opaque>",
  "jit_config": "<base64 GitHub JIT runner configuration>"
}
```

No shell command, argv array, filesystem path, environment mapping, UID/GID,
device list, network rule, cache path, or arbitrary systemd property is accepted
from the controller.

Those values are resolved exclusively from the root-owned project manifest.

## Validation

Reject unless all conditions hold:

1. request schema is exact;
2. `project_id` exists in the root-owned manifest registry;
3. `profile` is allowed for that project;
4. `runner_name` matches the project runner-name prefix;
5. `request_id` has not been accepted before;
6. JIT config is non-empty and below the configured size limit;
7. project concurrency is below the manifest maximum;
8. requested heavy profile, if any, has an externally recorded task
   authorization gate;
9. runner package and scale-set client pins match the root-owned lock file.

The provisioner must never decode the JIT payload in order to derive privilege.
It is secret job configuration, not policy input.

## Launch

For an accepted request the provisioner:

1. creates a fresh root-owned job directory with a random opaque job ID;
2. populates it from the trusted pinned Actions runner package;
3. chowns only the job tree and ephemeral staging cache to the project UID;
4. mounts or exposes trusted caches read-only;
5. launches a fixed runner command inside the project's systemd profile;
6. passes the JIT payload only as
   `ACTIONS_RUNNER_INPUT_JITCONFIG`;
7. records the request ID, project/profile, unit name, runner name, timestamps,
   and non-secret resource metadata.

The JIT value must never appear in command-line arguments, logs, filenames,
journal fields, crash dumps, or persisted receipts.

## Completion

After the runner exits, succeeds, fails, or times out:

1. collect/redact runner `_diag` logs into the project log root;
2. stop/kill the whole transient cgroup;
3. assert no project-UID process remains;
4. assert no assigned-GPU process remains;
5. remove runner configuration and job workspace;
6. remove candidate-writable staging cache;
7. preserve only explicitly trusted/promoted cache objects;
8. emit a non-secret cleanup receipt.

Any failed cleanup makes the project lane BLOCKED until a human/root recovery
procedure clears it.

## Forbidden provisioner behavior

The root helper must not:

- execute a command supplied by the controller;
- accept a path supplied by the controller;
- accept arbitrary environment variables;
- expose a shell;
- proxy GitHub credentials;
- clone repositories;
- upload artifacts;
- edit project code;
- use Docker;
- alter production services;
- widen a project's manifest privileges dynamically.

## Kill switch

A separate root-owned kill switch must be able to disable the listener, reject
new requests, terminate all `workspace-ci-*.scope/service` units, archive
diagnostics, and leave production projects/services unchanged.
