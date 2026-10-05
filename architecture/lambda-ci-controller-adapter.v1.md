# Lambda CI Controller Adapter v1

Status: static P1 design.

## Upstream pin

Use `actions/scaleset@e6daac702355cdb5b880b4fbdcf6d85dcd9e48e5`.
Do not use a floating branch/tag in the installed controller.

## Responsibility

The unprivileged `ci-controller` process owns only:

- repository-scoped GitHub App/PAT authentication;
- scale-set lifecycle;
- listener/message polling;
- job acquisition;
- JIT runner-config generation;
- request submission to the local root provisioner.

It does not:

- clone repositories;
- execute project code;
- create users;
- invoke arbitrary systemd commands;
- choose paths/devices/resources;
- read `/home/atrott`;
- reach production services intentionally;
- own root credentials.

## Scale-set settings

Initial research-engine pilot:

- name: `lambda-research-engine`
- scope: repository `adamtrott78/research-engine`
- min runners: 0
- max runners: 1
- DisableUpdate: true
- runner names prefixed `lambda-research-engine-`

Use `statistics.TotalAssignedJobs` as the scaling signal, matching upstream guidance.

## Provision request

For each required runner:

1. generate a JIT config with the pinned scale-set client;
2. construct the strict provisioner request from
   `architecture/lambda-ci-provisioner-protocol.v1.md`;
3. send over the root-owned Unix socket;
4. never log the JIT payload;
5. retain only request ID, runner name, project/profile, and non-secret lifecycle
   status.

## Profile selection

The scale-set label itself does not grant arbitrary privilege.

For v1, each trusted workflow targets exactly one allow-listed profile through
a controller-side mapping owned outside candidate branches.

Candidate code cannot ask the root provisioner for a profile directly.

## Credentials

Preferred: private GitHub App installed only on opted-in repositories.

The App private key and installation metadata are readable only by
`ci-controller`, not project runner UIDs or root provisioner code.

## Update policy

Because `actions/scaleset` is Public Preview, upgrades require:

- explicit new commit pin;
- source/release review;
- controller unit tests;
- no-op scale-set regression;
- P3 CPU validation;
- P4 GPU validation before replacing the accepted installed build.
