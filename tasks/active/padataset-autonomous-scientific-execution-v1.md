<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: padataset-autonomous-scientific-execution-v1
- Title: PADataset autonomous scientific execution v1
- Status: IN_PROGRESS
- Capsule schema: v2
- Current stage: scientific_activation_validation

## Goal

Make PADataset scientific GPU experiments autonomously executable by ChatGPT through the existing self-hosted Lambda control plane using an exact root-owned DNNs runtime, exact PR-head provenance, read-only project data/cache authority, bounded experiment request schemas, durable artifacts/receipts, and no per-run operator terminal work.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: padataset-autonomous-scientific-execution-v1
- Remote checkpoint: bb6528faf9643ffddf517891eba70f7988267d40
- Remote verified: false

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 100888178f362094c45807817f992d2653dcb7b2
- Remote verified: true

## Next safe action

Perform a two-phase, rollback-safe storage migration of /srv/workspace-ci/padataset/expanded-runtimes and /srv/workspace-ci/padataset/trusted-cache to /data/workspace-ci/padataset using rsync -aHAX --numeric-ids, checksum verification, then bind mounts at the original paths and persistent /etc/fstab entries. Keep the original root copies renamed as rollback until post-cutover verification succeeds; only then delete them to reclaim ~80.56 GiB. Do not move the mutable source DNNs venv or PADataset feature cache.

## Remaining work

- Contain the v3 control-small controller restart storm and recover after the GitHub REST primary-rate-limit window resets; preserve validation #466 without duplicate requests.
- Once #466 runs, require SUCCESS or diagnose its exact failure. Then recheck main and integrate current main into the activation branch with unchanged scientific tree, followed by exact-head validation of the integrated SHA.
- Advance the validated integrated policy to main so Lambda CI Project Reconcile installs the exact runtime/data/contract/route policy.
- Verify live reconciliation and run autonomous scientific smoke, bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation.
- Track the v3 controller 403 rate-limit handling defect for a separately authorized infrastructure hotfix; current code retries 429/5xx but treats primary-rate-limit 403 as fatal.

## Blockers / gates

- Dedicated exact-head Lambda CI Workspace Control Validation #466 / run 43149651861 / job 130955554208 remains queued without runner assignment.
- workspace-ci-v3-controller@workspace-control-control-small-v1.service is intentionally stopped/inactive at NRestarts=3495 after a GitHub primary-rate-limit 403 restart storm; a fresh post-reset authenticated rate-limit probe is required before restart.
- Exact disk attribution proves the PADataset promotion added 80.56 GiB of physical duplicate storage on the root NVMe: promoted DNNs runtime 7.38 GiB plus promoted scientific cache 73.18 GiB. Source and promoted copies are on the same ext4 root filesystem, so reflink sharing did not occur.
- A separate /data ext4 volume has ~569 GiB free. Preferred remediation is to move only immutable promoted expanded-runtimes and trusted-cache backing stores to /data and bind-mount them back at their existing /srv/workspace-ci/padataset paths, preserving all absolute-path provenance and policy bindings.
- Scientific route must not be reconciled or invoked until exact-head validation and live reconciliation succeed.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
