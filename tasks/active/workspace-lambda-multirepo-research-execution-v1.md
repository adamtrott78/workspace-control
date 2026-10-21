<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-multirepo-research-execution-v1
- Title: Workspace Lambda Multi-Repository Research Execution v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Generalize the accepted GitHub-to-Lambda execution substrate from a research-engine-specific pilot into a reusable, fail-closed, manifest-driven research compute control plane that can execute bounded candidate code from research-engine, PADataset, and future explicitly authorized research repositories without per-task controller/provisioner/runtime patches or routine human SSH/sudo intervention.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: f924f2bf45fbf05aa3f0dc2ea036354143834246
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: a4a5e1a2afc004b484542d5a71746e6472154fdb
- Remote verified: true

## Next safe action

SECOND VALIDATED RESPONSE-LIVENESS REPLAY FAILED CLOSED AFTER RUN3_BOOT_SOCKET_ISOLATION=PASS. Keep all affected services disabled/contained and preserve root receipt 463f3e92-087e-5c68-9fec-c4098df8ab7e. Run the bounded read-only post-attempt diagnostic for the latest attempt: current service states/restart counts, controller last-success.json and last-rejected.json, root receipt inventory and selected receipt content, and controller/root journals beginning at 2026-10-21 18:30 local time. Use the repaired controller's journal status lines to distinguish TRANSIENT_ERROR, NO_CURRENT_SUCCESSFUL_RECONCILIATION_RUN, root socket response, state-write failure, or another exception. Do not rerun recovery, delete receipts, change policy, bump registry_epoch, restage the token, or onboard PADataset.

## Remaining work

- Run 3 immediate: perform a bounded read-only post-second-attempt diagnostic. Inspect controller last-success/last-rejected state, root receipt inventory/mtime, workspace-ci-reconcile-controller.service journal, workspace-ci-reconciler.service journal, and current service states from the response-liveness attempt. Classify whether the repaired controller reached root, emitted TRANSIENT_ERROR, selected no current successful run, received PASS but failed state persistence, or hit another transport boundary.
- Run 3: checkpoint the accepted Git-driven reconciliation controller/root path; only then mark git_driven_project_reconciliation VALIDATED.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- Exact validated response-liveness recovery still produced no controller last-success despite source/installed-state/socket-isolation PASS. Rollback completed and services are disabled/contained. Do not rerun or patch again until second-attempt controller/root journals and persistent state prove the remaining failure mode.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
