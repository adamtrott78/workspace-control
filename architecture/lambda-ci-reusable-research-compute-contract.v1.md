# Reusable Research Compute Operating Contract v1

Status: **FROZEN AFTER RUN-4 ACCEPTANCE**

This contract defines the supported onboarding surface for an additional research
repository after the accepted research-engine migration and PADataset second-project
pilot.

## Accepted substrate

The reusable substrate consists of:

- the generic GitHub scale-set controller;
- root-owned project registry and schema-v2 project manifests;
- semantic execution contracts;
- the generic provisioner and privileged runtime;
- the root reconciliation service and unprivileged reconciliation controller;
- root-owned systemd templates;
- deterministic per-project identity, roots, scale sets, runner prefixes and
  transient-unit namespaces.

Research-engine and PADataset are the live acceptance oracles. A new project does
not get additional privileged authority merely because it has a new route name.

## Supported project-onboarding surface

Adding another approved repository is a **declarative operation** when its needs fit
an already accepted execution contract.

The allowed onboarding changes are:

1. Add the target repository's thin workflow launchers.
2. Bind each launcher by exact default-branch Git blob.
3. Add one project entry to
   `architecture/lambda-ci-project-registry.v1.json`.
4. Add one schema-v2 project manifest defining repository identity, routes,
   existing semantic execution-contract bindings, actor/PR gates and optional
   exact model/runtime bindings.
5. Advance the registry epoch.
6. Pass Workspace Control Validation.
7. Require a fresh successful trusted reconciliation workflow for the exact
   policy-changing commit.
8. Let the accepted reconciliation plane add/update the derived system identity,
   project roots and controller instances.
9. Run bounded non-scientific canaries and verify root cleanup/isolation before
   scientific use.

Project identity is derived from `project_id`:

- user/group: `ci-{project_id}`;
- project root: `/srv/workspace-ci/{project_id}`;
- CPU scale set: `lambda-{project_id}`;
- GPU scale set: `lambda-{project_id}-gpu`;
- CPU/GPU runner prefixes follow the same deterministic namespace;
- controller instances are
  `workspace-ci-controller@{project_id}-cpu.service` and
  `workspace-ci-controller@{project_id}-gpu.service`.

## What must not change for ordinary onboarding

Ordinary project onboarding must not require changes to:

- `controller/lambda-ci-controller/`;
- `scripts/lambda_ci_provisioner.py`;
- `scripts/lambda_ci_provisioner_service.py`;
- `scripts/lambda_ci_runtime.py`;
- `scripts/lambda_ci_reconciler.py`;
- `scripts/lambda_ci_reconcile_controller.py`;
- installed generic systemd service templates;
- privileged runtime dispatch code.

If a project cannot be onboarded without changing one of those surfaces, the work
is **not** ordinary onboarding. It is a new substrate/authority change and requires
a separately reviewed implementation and acceptance cycle.

## Execution-contract rule

Route names carry no privileged meaning.

A new route may reuse an accepted contract such as:

- `cpu-public-ci-v1` for bounded CPU execution;
- `gpu-single-public-ci-v1` for bounded single-GPU execution.

A capability not represented by an accepted execution contract remains denied.
For example, the generic dual-GPU public compute contract remains unavailable
while its lifecycle is not accepted.

Model/runtime mounts require exact root-owned bindings when the selected execution
contract requires them. A project with no such bindings receives none.

## Public-repository rule

Public projects retain the PADataset acceptance boundary:

- explicit allowed actor(s);
- issue-comment trigger bound to a trusted workflow blob;
- candidate must equal the current head of an open same-repository PR;
- fork/foreign PR execution is denied;
- target repositories cannot invoke root reconciliation or choose privileged
  paths, users, devices, systemd properties or commands.

## Isolation and cleanup acceptance

Before a newly onboarded project is accepted, prove:

- a unique project UID/GID;
- sibling project mutable roots are unreadable/unwritable/untraversable;
- control-plane state is inaccessible;
- only root-authorized GPU devices are visible;
- runner and staging workspaces are destroyed after each canary;
- project CPU/GPU process residue is zero;
- no lane quarantine remains;
- generic installed source blobs are unchanged;
- all existing projects still pass non-regression;
- controller/provisioner/reconciler services remain stable.

## Third-project executable proof

`tests/fixtures/lambda-ci-project-future-research.v2.json` is a non-live synthetic
third-project manifest. It is intentionally **not** added to the live registry.

`tests/test_lambda_ci_third_project_reuse.py` proves against the real generic
code that adding a synthetic registry entry plus that manifest is sufficient to:

- derive `ci-future-research`, project roots and CPU/GPU scale sets;
- produce an ADD_OR_UPDATE reconciliation plan with both controller instances;
- mint CPU and single-GPU admission using existing execution contracts;
- build generic launch specifications with no model/runtime binding;
- preserve public-repository fork denial;
- render non-secret controller environments.

The proof changes no controller, provisioner, runtime, reconciler, systemd template
or live registry entry.

## Operational conclusion

After Run 4, the platform boundary is:

**new approved repository + thin launchers + registry entry + project manifest +
accepted execution contracts + trusted reconciliation + canary acceptance**.

Routine project onboarding no longer requires per-task controller/provisioner/runtime
patches or routine SSH/sudo implementation work. Root intervention remains reserved
for exceptional authority changes, removal, credential administration, or failures
that cross the accepted reconciliation/runtime boundary.
