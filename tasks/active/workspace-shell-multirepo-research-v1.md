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

Validate this exact final-quarantine authority snapshot. After PASS, perform the root-owned refresh. Do not route scientific training through the existing PADataset gpu-ci canary because its accepted state effect is CI_VALIDATION_ONLY.

## Remaining work

- Validate this final state-only authority snapshot binding PADataset be04a4a4428a3c57233fc1ee598b4311ece96587.
- Operator performs one final root-owned Workspace Shell snapshot refresh.
- Verify exact live bindings and rerun the expanded deterministic contract test.
- Operator launches the frozen PA2 backbone in the existing DNNs scientific environment, or separately authorizes a new scientific GPU execution-contract project.
- After the backbone completes, run Architecture C small-real evaluation and validate result_record.json.

## Blockers / gates

- Live Workspace Shell has not yet been rebound from PADataset 694a0c828ed4c8e8d02a344eb2451905e171aaca to final quarantine source be04a4a4428a3c57233fc1ee598b4311ece96587.
- After the final live refresh, scientific GPU execution still cannot be launched through connected tools: the only accepted PADataset GPU execution contract is CI_VALIDATION_ONLY and Workspace Shell intentionally lacks the user's PyTorch DNNs runtime.
- Creating a scientific-training execution contract would be a new substrate/authority capability and is outside the current accepted task authority.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
