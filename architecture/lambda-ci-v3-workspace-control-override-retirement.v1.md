# Workspace-control V3 class-specific controller override retirement v1

## Purpose

Retire the stale class-specific controller executable created by the reviewed
PR #604 terminal-revival transaction so
`workspace-ci-v3-controller@workspace-control-control-small-v1.service`
returns to the exact shared V3 controller installed by the later transactional
controller refresh.

The transaction exists only because the class-specific `ExecStart` drop-in
shadows the shared controller path. It does not change controller semantics,
workflow state, scheduler state, policy, credentials, scale sets, provisioner
state, or sibling controller services.

## Frozen live bindings

The operator requires:

- shared controller source head:
  `e0911a56a8e0088d7b90728b7d603dc1f73f824a`;
- shared controller SHA-256:
  `644d34b02e2166a1c24ffba48e71302f8519a807c872b45a367285146e407918`;
- stale PR #604 override SHA-256:
  `9db8161340baacd7d7aad48ad47e013651158748bfd61b13c41ab29539a35af3`;
- exact stale override path:
  `/opt/workspace-ci/v3/controller-overrides/workspace-control-control-small-v1/lambda-ci-controller-v3`;
- exact stale drop-in:
  `/etc/systemd/system/workspace-ci-v3-controller@workspace-control-control-small-v1.service.d/99-terminal-revival-reviewed.conf`;
- controller policy SHA-256:
  `870feb9835230c1d9dd897d9fe64b7c1c23def4d5d0bd1e`.

The active controller-refresh receipt must bind the exact shared source head and
binary digest and remain in `ACTIVE` phase.

## Pre-mutation gates

The target service must be loaded, active/running, execute the exact stale
override bytes, and run as `ci-ctl-wc-control:ci-gh-workspace-control`.

The exact #484 scheduler ledger key must still be absent and no durable record
for the current controller-policy generation may be nonterminal. The source
checkout must be detached, exactly bound to the approved transaction head, and
completely clean including untracked files.

Sibling V3 service generations are snapshotted before mutation.

## Mutation boundary

The operator stops only the target workspace-control V3 controller and waits
for `inactive/dead` with MainPID 0. It then rechecks that scheduler authority
has not advanced.

The stale executable and drop-in are moved into the root-private transaction
directory as rollback material. The operator performs one `daemon-reload`,
starts only the target service, and requires the live process to execute the
exact shared controller path and SHA-256 above.

Sibling service generations must remain byte-for-byte equivalent at the
systemd property snapshot boundary. Installed-generation verification must
also pass.

## Rollback boundary

Before scheduler mutation, failure may restore the exact stale executable and
drop-in from the transaction directory, daemon-reload, and restart only the
target service.

If the #484 ledger appears or another current-policy nonterminal record exists
after the shared controller was started, rollback to the stale controller is
forbidden. The transaction records
`POST_SCHEDULER_MUTATION_NO_ROLLBACK` and leaves the accepted shared
controller as the active authority.

## Explicit non-authority

This transaction may not:

- write, delete, or restore any scheduler ledger;
- dispatch, rerun, or cancel GitHub Actions;
- replace the shared controller binary;
- modify controller policy, credentials, root policy, or workflow pins;
- mutate provisioner state;
- restart PADataset or research-engine controllers;
- activate or mutate retired V2 workspace-control infrastructure.
