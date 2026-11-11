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

Validate this exact state-only authority snapshot. No scientific GPU execution is authorized until the new PADataset head is installed and the expanded deterministic contract test passes.

## Remaining work

- Validate this state-only authority snapshot binding PADataset 694a0c828ed4c8e8d02a344eb2451905e171aaca.
- After PASS, operator refreshes the root-owned Workspace Shell PADataset snapshot.
- Rerun the expanded deterministic contract test, now including the frozen PA2 backbone config assertions.
- Train the frozen PA2 four-class known-only backbone in the sanctioned DNNs scientific environment.
- Run Architecture C small-real evaluation and validate result_record.json.

## Blockers / gates

- Live Workspace Shell is still bound to PADataset 81ee9bf2a06949ce1e9477befe00f833248d8ea3; new backbone-ready source 694a0c828ed4c8e8d02a344eb2451905e171aaca is not installed yet.
- Real backbone training/evaluation requires a PyTorch-capable scientific runtime; Workspace Shell remains intentionally bounded and does not expose the user's /home Conda environment.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
