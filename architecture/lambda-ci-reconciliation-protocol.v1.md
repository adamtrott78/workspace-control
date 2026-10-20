# Lambda CI Project Reconciliation Protocol v1

Status: **design-only; not installed.**

## Purpose

Turn a reviewed workspace-control project-registry change into bounded root-owned host configuration without routine operator SSH/sudo.

This is not a generic root executor.

## Trust split

- GitHub-facing reconciliation controller: unprivileged; owns GitHub App access for workspace-control only.
- Root reconciler: credential-blind; owns deterministic user/directory/config/systemd reconciliation.
- Target project runners: cannot access the reconciliation socket and cannot submit reconciliation requests.

## Source attestation

A request is considered only when the controller verifies:

- repository `adamtrott78/workspace-control`;
- default branch `main`;
- exact trusted reconciliation workflow path/blob;
- exact default-branch commit;
- allowed actor;
- terminally valid GitHub workflow/job identity.

Root compares those fields to the installed reconciliation ceiling.

## Request payload

The request follows `schemas/lambda-ci-reconciliation-request.v1.schema.json`.

It carries only:

- source attestation;
- complete project-registry JSON + digest;
- complete referenced project-manifest JSON documents + digests;
- dry-run flag.

No command, argv, target path, unit text, UID/GID, device list, network rule, credential, or arbitrary environment is accepted.

## Root validation order

1. strict request schema;
2. source attestation matches installed workspace-control reconciliation policy;
3. canonical JSON digests match;
4. project-registry schema;
5. every referenced project manifest present exactly once;
6. project-manifest schema;
7. repository owner is allowed;
8. deterministic identity/path/scale-set/prefix derivations match;
9. every route resolves to a known execution contract;
10. active routes have exact non-null trusted workflow blob;
11. public repositories require same-repository PR heads, fork denial and explicit actors;
12. requested changes fit installed reconciliation ceiling;
13. dry-run diff is deterministic.

Unknown/extra state fails closed.

## V1 allowed root effects

Root-owned implementation may:

- create deterministic `ci-<project>` user/group;
- create deterministic project roots/subdirectories;
- install validated registry/project/controller config under fixed roots;
- instantiate root-owned controller systemd templates;
- start/restart affected controller instances;
- preserve/health-check unchanged projects;
- write a reconciliation receipt.

It may not remove a project, delete project data, promote trusted cache objects, execute project code, mutate production/scientific state, install arbitrary packages, or run arbitrary shell from the request.

## Replay

A reconciliation request is keyed by request ID + canonical source commit + registry/manifests digest set.

- identical completed request -> return existing receipt, no repeated mutation;
- same request ID with different digest -> reject;
- interrupted request -> recover from before/after installed digests; never blindly replay destructive steps;
- project removal -> reject in v1.

## One-time migration

The generic reconciler/controller templates themselves require one bounded root installation after Run-2 validation. That installation is the last planned routine sudo boundary.

Afterward, approved project add/update operations use this protocol.
