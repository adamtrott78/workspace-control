# Expanded Qwen Runtime Drift Recovery

Status: **BLOCKING PREREQUISITE**

This file is durable incident-recovery context for
`workspace-lambda-execution-policy-v1`. It exists because the normal task
capsule/handoff state was stale when runtime drift was discovered.

## Authority and scope

This incident blocks the two remaining root-authored dual failure gates.
Do not redesign dual-GPU policy, activate `model-eval-dual-gpu`, merge the
activation PR, trigger the dual Qwen pilot, rerun the accepted single-GPU
pilot, or rerun the already-accepted dormant two-GPU NCCL host gate.

Canonical expanded runtime:

`/srv/workspace-ci/research-engine/expanded-runtimes/qwen35-vllm-cu129-image-native-sampler-v3/f67ff9a26690c55930232c915e59e826e3cca2dd89012de9e35a852032b38f74`

Accepted identity:

- tree digest: `b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63`
- files: `53583`
- directories: `6069` including runtime root
- symlinks: `4`
- materialized regular-file bytes: `11067818797`
- source manifest: `f67ff9a26690c55930232c915e59e826e3cca2dd89012de9e35a852032b38f74`
- trusted wheel-bundle object:
  `/srv/workspace-ci/research-engine/trusted-cache/objects/runtime/sha256/23a47f27bdb6bec63955b901080fc0926cffee8cf081d010195613789bc5bbf4`

Observed drifted tree:

- files: `54451`
- directories: `6241`
- symlinks: `4`
- exact aggregate delta: `+868 files / +172 directories / +0 symlinks`

The canonical runtime is currently restored to the pre-repair drifted state
after failed replacement attempts.

## What was proven

The original dual-timeout launch did not reach the intended physical timeout.
Production pre-verification failed on a writable
`lib/python3.12/site-packages/__pycache__` inode.

A naive theory that every `__pycache__` path was drift was disproven.
The drifted tree contains 1279 files and 223 directories under
`__pycache__`, while total drift is only 868 files and 172 directories.
The accepted baseline therefore already contained substantial
`__pycache__` material.

Fresh-rebuild experiments established that:

- trusted uv 0.12.23 is valid;
- the trusted 196-wheel source object is valid;
- exact 196-package installation works;
- Qwen3_5ForConditionalGeneration import works;
- a fresh runtime can be built at private canonical-path semantics;
- fresh trees do **not** reproduce the historical accepted expanded-tree
  digest byte-for-byte.

Every live replacement attempt rolled back. Do not use fresh reconstruction as
the repair method.

## Recovery invariant

Preserve the existing drifted tree.

A disposable reconstruction may be used only as a **candidate path-set oracle**.
It is not the accepted baseline.

Before any live mutation, compute a purely virtual projection of the existing
tree:

1. derive a proposed extra-path exclusion set;
2. exclude only those proposed extra paths virtually;
3. for retained regular files/directories, project mode as
   `current_mode & ~0o222`;
4. preserve every other mode bit and every retained file byte/link target;
5. compute projected counts, regular-file bytes, and exact production tree
   digest without changing the live tree.

The production digest record format is:

- directory: `D<NUL><relative-path><NUL><octal-mode><LF>`
- symlink: `L<NUL><relative-path><NUL><link-target><LF>`
- regular file:
  `F<NUL><relative-path><NUL><octal-mode><NUL><size><NUL><sha256(file-bytes)><LF>`

Use real NUL and LF bytes. The runtime root is not a digest record, but the
directory count includes it.

Projection may PASS only if all are exact:

- projected files: `53583`
- projected directories including root: `6069`
- projected symlinks: `4`
- projected regular-file bytes: `11067818797`
- projected digest:
  `b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63`

If any value differs, stop with zero live mutation.

## Mutation rule after projection PASS only

Only after exact projection PASS may a separate reversible mutation be designed.

- quarantine/move proposed extra paths outside the canonical runtime rather
  than immediately deleting them;
- preserve original modes needed for rollback;
- clear only write bits on retained regular files/directories;
- run the authoritative production verifier immediately;
- require exact accepted digest/counts, root ownership, and no writable inode;
- on any mismatch, restore quarantined material and original modes;
- restore control-plane services only after exact accepted verification or
  successful rollback.

No timeout/OOM gate runs during recovery.

## Historical evidence

Original accepted-build evidence:

`~/adamArchives/Adam/workspace-control-tmp/qwen35-expanded-runtime-20261008T050010Z`

Known files:

- `build-identity.json`
- `tree-evidence.json`
- `canary.json`
- `mount.txt`
- `uv-build.log`

Durable expanded-runtime receipt:

`/var/lib/workspace-ci/expanded-runtime-receipts/f67ff9a26690c55930232c915e59e826e3cca2dd89012de9e35a852032b38f74.json`

These establish aggregate accepted identity. No recovered artifact contains a
complete historical per-path accepted manifest, tar/archive, snapshot, reflink,
or untouched hardlink clone.

## Accepted gates that must not be replayed

The dormant two-GPU NCCL host acceptance already passed before this incident:
both A4500 ranks completed the real NCCL all-reduce to 3.0, cleanup passed,
controllers were healthy, and dual admission/model inference remained off.

Do not rerun that gate.

## Immediate next safe action

Build and run the **read-only projection/classification gate** against the
existing drifted canonical tree.

The first required outcome is evidence answering:

> Is there a candidate exclusion set, with only virtual write-bit normalization,
> whose resulting virtual tree has exactly the accepted counts, accepted
> materialized bytes, and exact accepted digest `b0cbb4ef...`?

Until the answer is unequivocally YES, make zero further mutations to the
canonical expanded runtime.

## Validated projection helper

Use only `scripts/runtime_tree_projection.py` from workspace-control commit
`7d6a7e46557342fdf085e1202970ff200016f547` (blob `0974a03d46c487b32801e88647cba489f363a64d`).

PR #196 passed Workspace Control Validation run `39182798953` before merge.
The helper is read-only with respect to both input trees and records evidence
outside the runtime. It uses the disposable reference only as a path/type oracle;
all projected bytes, modes, ownership checks, sizes, symlink targets, and the
final digest come from the existing live canonical tree.

## Projection PASS evidence

Read-only projection completed successfully on 2026-10-19.

- candidate extras: 868 files / 172 directories / 0 symlinks
- reference-only paths: 0
- type mismatches: 0
- non-__pycache__ extras: 0
- projected tree: 53583 files / 6069 directories / 4 symlinks
- projected materialized bytes: 11067818797
- projected digest: `b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63`
- retained non-root-owned paths: 0
- retained writable paths: 0
- live runtime mutated: false

Evidence directory:
`/home/atrott/adamArchives/Adam/workspace-control-tmp/runtime-drift-projection-20261019T010548Z`

Evidence SHA-256:

- live tree: `0425192015698c4440395cc1b011137fd8f03662e8c10f84b9c563b16e9c020d`
- candidate difference: `4aedbbc374255ba17d21a82a13be6e3d719f25a864e3b88ba44384d0c4f12ad5`
- projection summary: `b70cf7b8d03a3f26acfec04117a1d30b80b7b695439e4e1b54320504a9120eda`

## Validated reversible correction helper

Use only `scripts/runtime_tree_repair.py` from workspace-control commit
`d479db58a0edd71f458894590536ea83791e8104`
(blob `82d1743567d5f0e0c18de315594d95f3908c4afe`).

PR #198 passed Workspace Control Validation run `39184369750` before merge.
The helper revalidates the exact projection before action, moves only minimal
candidate roots to same-filesystem quarantine, verifies the resulting tree
against the accepted digest, and retains a manifest for rollback.

## Authoritative restoration PASS

The reversible path-only correction completed successfully.

- candidate roots quarantined: 172
- quarantine: `/srv/workspace-ci/research-engine/runtime-recovery-quarantine/f67ff9a-20261019T012703Z`
- repair manifest SHA-256: `32f71d395f7dfe7acb87061a905e94429d3e08e876c9c0c7c895d8b327e6e37b`
- authoritative file count: 53583
- authoritative directory count: 6069
- authoritative symlink count: 4
- authoritative tree digest: `b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63`
- read-only hardened: true
- receipt verified: true
- all three control-plane services active with NRestarts=0
- project CPU/GPU residue: zero
- timeout/OOM gates were not run during recovery

Run evidence:
`/home/atrott/adamArchives/Adam/workspace-control-tmp/runtime-drift-repair-20261019T012703Z`

This incident is closed as VALIDATED. Resume the owning dual-GPU failure gates
without replaying the accepted dormant NCCL gate.
