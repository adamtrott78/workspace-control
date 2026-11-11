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
- Remote checkpoint: 81ee9bf2a06949ce1e9477befe00f833248d8ea3
- Remote verified: true

## Next safe action

Operator-only root gate: install authority 157aaf72e9e5761c8d7140a96d986e2e742a5a9c, workspace-control execution f7ed7305e904ec24a444f7a488ca07e9bef4fdc7, and PADataset 81ee9bf2a06949ce1e9477befe00f833248d8ea3. Connected Workspace Shell cannot mutate the root-owned runtime snapshot.

## Remaining work

- Operator installs validated authority 157aaf72e9e5761c8d7140a96d986e2e742a5a9c, workspace-control f7ed7305e904ec24a444f7a488ca07e9bef4fdc7, and PADataset 81ee9bf2a06949ce1e9477befe00f833248d8ea3 using the existing rollback-capable upgrade.
- Verify live exact bindings and rerun tests/test_multisurrogate_dqnguard.py through research-bounded.
- Prepare the known-only target-fold backbone with cache_len=16384.
- Use a sanctioned PyTorch-capable scientific compute surface for Architecture C small-real execution.

## Blockers / gates

- Remaining action is root-owned Workspace Shell snapshot replacement. Privileged helper trust is intentionally empty/fail-closed, so connected Workspace Shell cannot perform it.
- Live runtime has not yet been rebound to workspace-control f7ed7305e904ec24a444f7a488ca07e9bef4fdc7 and PADataset 81ee9bf2a06949ce1e9477befe00f833248d8ea3.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
