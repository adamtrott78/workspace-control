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
- Remote checkpoint: be04a4a4428a3c57233fc1ee598b4311ece96587
- Remote verified: true

## Next safe action

Operator-only root gate: install authority 0c39bad0219d553fcd1ee8780374412ab9efab46, workspace-control f7ed7305e904ec24a444f7a488ca07e9bef4fdc7, PADataset be04a4a4428a3c57233fc1ee598b4311ece96587. Then ChatGPT verifies the live state. Scientific GPU training itself remains a separate operator surface unless a new scientific execution contract is explicitly authorized.

## Remaining work

- Operator installs authority 0c39bad0219d553fcd1ee8780374412ab9efab46, workspace-control f7ed7305e904ec24a444f7a488ca07e9bef4fdc7, and PADataset be04a4a4428a3c57233fc1ee598b4311ece96587.
- Verify exact live bindings and rerun the 8-test deterministic Stage 03 contract.
- Operator launches the frozen PA2 backbone in the existing DNNs scientific environment using a clean exact-SHA checkout; historical evidence checkout remains untouched.
- After backbone completion, inspect exact artifacts, run Architecture C small-real evaluation, and validate result_record.json.

## Blockers / gates

- Live Workspace Shell remains bound to PADataset 694a0c828ed4c8e8d02a344eb2451905e171aaca until operator installs validated authority 0c39bad0219d553fcd1ee8780374412ab9efab46 with PADataset be04a4a4428a3c57233fc1ee598b4311ece96587.
- After that refresh, connected execution still cannot perform the actual scientific GPU training: accepted PADataset gpu-ci uses gpu-single-public-ci-v1 with state_effect_class=CI_VALIDATION_ONLY, and Workspace Shell intentionally lacks the DNNs/PyTorch runtime.
- A new scientific-training execution contract would expand privileged execution authority and requires a separate explicitly reviewed task; it cannot be inferred from the current research task.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
