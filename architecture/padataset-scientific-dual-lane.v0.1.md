# PADataset Scientific Dual-Lane v1

Status: **CANDIDATE — NOT LIVE**

## Goal

Permit at most two concurrent PADataset scientific experiments while preserving the existing invariant that each JIT runner sees exactly one root-authorized GPU.

## Topology

- Lane A remains `padataset-scientific-single-gpu-v1`, pinned to GPU0 `GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea`.
- Lane B is `padataset-scientific-single-gpu-2-v1`, pinned to GPU1 `GPU-cfed3394-a935-63aa-9325-c4cae7b568b6`.
- Lane B uses its own controller Unix user, scale set, runner prefix, execution contract, systemd profile, trusted workflow, route, and artifact namespace.
- Both lanes bind the same exact read-only `padataset-dnns-v1` runtime and trusted scientific-data profile.
- The root provisioner remains the only physical-resource allocator.

## Concurrency policy

- Host active-runner ceiling: 2.
- PADataset project ceiling: 2.
- Workspace Control and Research Engine project ceilings remain 1.
- Each scientific class has `max_runners=1`.
- GPU claims remain atomic and exclusive; lane A and lane B claim disjoint GPU UUIDs.

## Activation safety

The repository candidate may be built and validated while a scientific job is running because it does not mutate the live host. Live activation is forbidden until all of the following are true:

1. no queued/in-progress PADataset scientific workflow run;
2. no nonterminal lane-A or lane-B controller ledger record;
3. no active/held provisioner record for either scientific class;
4. no scientific transient runner/supervisor unit;
5. PADataset main contains the exact reviewed lane-B workflow blob;
6. the lane-B GitHub scale set exists with zero assigned/running jobs;
7. the current effective live v3 override chain verifies before mutation;
8. a fresh one-shot root/operator authority receipt binds the exact candidate generation.

Activation must be additive. Existing lane A is not restarted or rewritten merely to install lane B. Any failure before lane-B activation leaves lane B disabled and preserves lane A.

## Non-goals

- No job may see both GPUs.
- No candidate or workflow input selects a GPU UUID.
- No dynamic GPU pooling is introduced in v1.
- No live mutation is authorized by this document or by the candidate PR alone.
