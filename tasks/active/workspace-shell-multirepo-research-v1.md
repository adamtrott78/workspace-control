<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-multirepo-research-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-multirepo-research-v1
- Title: Workspace Shell multi-repo PADataset research access v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Extend the live Workspace Shell v1 lineage with a first-class PADataset target that supports exact-SHA/task-bound Git provenance, bounded read-only evidence inspection, and sandboxed network-denied research execution without exposing a generic shell or making the historical PADataset checkout writable.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-multirepo-v3-reconcile-20261111
- Remote checkpoint: f7ed7305e904ec24a444f7a488ca07e9bef4fdc7
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 694a0c828ed4c8e8d02a344eb2451905e171aaca
- Remote verified: true

## Next safe action

Operator-only root gate: install authority f7b8a40f9f50e584974fac92e5eef4773405606b, workspace-control f7ed7305e904ec24a444f7a488ca07e9bef4fdc7, and PADataset 694a0c828ed4c8e8d02a344eb2451905e171aaca. After PASS, ChatGPT must verify the live bindings and run the expanded deterministic contract test before scientific GPU training.

## Remaining work

- Operator installs authority f7b8a40f9f50e584974fac92e5eef4773405606b, workspace-control f7ed7305e904ec24a444f7a488ca07e9bef4fdc7, PADataset 694a0c828ed4c8e8d02a344eb2451905e171aaca.
- Verify exact live bindings and run the expanded deterministic Stage 03 contract test.
- Train the frozen PA2 backbone config in the DNNs PyTorch scientific environment.
- Run Architecture C small-real evaluation and validate result_record.json.

## Blockers / gates

- Live Workspace Shell remains bound to PADataset 81ee9bf2a06949ce1e9477befe00f833248d8ea3 until the operator installs validated authority f7b8a40f9f50e584974fac92e5eef4773405606b with PADataset 694a0c828ed4c8e8d02a344eb2451905e171aaca.
- Connected Workspace Shell cannot perform the root-owned snapshot replacement because privileged helper trust is intentionally empty/fail-closed.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
