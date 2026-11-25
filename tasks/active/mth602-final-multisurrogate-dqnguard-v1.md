<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-final-multisurrogate-dqnguard-v1
- Title: MTH 602 final project / PADataset multi-surrogate DQNGuard
- Status: CHECKPOINTED
- Capsule schema: v2

## Goal

Complete deterministic Stage-03 Architecture-C replication at the qualified detv2 profile on the proven dual-GPU PADataset scientific runtime, then compare seed0/seed1/seed2 before making any architecture change while preserving PA2 quarantine and known-only selection/threshold semantics.

## Repositories

### PADataset

- Intent: mutate
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

### workspace-control

- Intent: mutate
- Remote branch: padataset-lane-b-runner-identity-v1
- Remote checkpoint: fe9621d848ae3405006fb65e8e691080d66aeb69
- Remote verified: true

## Next safe action

On fresh-chat resume, first read this capsule and the exact PR #17 / PR #632 state, then inspect seed0 run 43751609944/job132926587786, seed1 run 43751622546/job132926629552, and automation 6af9be2287e08191b33ea0cb024c43c8. Do not duplicate seed0, seed1, seed2, or the automation. If seed0/seed1 are still running, continue monitoring through connected GitHub/automation surfaces. When the first lane frees, confirm whether the existing automation has already issued seed2; only one seed2 request may exist. Once all three deterministic detv2 replicates are terminal, validate their exact artifacts/invariants and compare outcomes before any Architecture-C change.

## Remaining work

- Monitor seed0 run 43751609944 / job 132926587786 and seed1 run 43751622546 / job 132926629552 to terminal; inspect exact logs, scientific artifacts, receipts, and result_record files.
- For every terminal replicate verify exact candidate befe383fd67c8bca8d8ce370344b33c7e13cd52f, deterministic_training=true, deterministic_profile=strict_tf32, PA2 quarantine, known-only checkpoint/threshold semantics, cache_len=16384, and target_labels_used_for_tuning=false.
- Allow the existing DQNGuard Replicate Watch automation to issue exactly one seed2 detv2 request on the first freed lane after exact-head and duplicate-comment checks; do not create a duplicate watcher or seed2 request.
- Track seed2 to terminal and validate its artifacts/receipt/result_record with the same scientific invariants.
- Compare deterministic seed0/seed1/seed2 outcomes, including known metrics, unknown AUROC, PA2 precision/recall/F1, OSR macro-F1, threshold, confusion/error structure, and reproducibility digests where available.
- Decide whether the low-PA2-recall / PA8-collapse pattern is stable across deterministic replicates or primarily training-variance-driven before changing Architecture-C.
- Persist the replicate comparison and resulting scientific decision in PADataset project-owned documentation/task state.
- Keep PADataset PR #17 and Workspace Control PR #632 unmerged unless separate explicit merge authority is granted.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
