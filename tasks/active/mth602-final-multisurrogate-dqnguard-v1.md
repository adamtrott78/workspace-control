<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-final-multisurrogate-dqnguard-v1
- Title: MTH 602 final project / PADataset multi-surrogate DQNGuard
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Provide Workspace Shell authority for the PADataset multi-surrogate DQNGuard project so Stage 00 can recover canonical MILCOM baseline/runtime provenance directly from the prepared Lambda checkout before architecture implementation.

## Repositories

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: be04a4a4428a3c57233fc1ee598b4311ece96587
- Remote verified: true

## Next safe action

After operator installs authority 0c39bad0219d553fcd1ee8780374412ab9efab46, verify PADataset be04a4a4428a3c57233fc1ee598b4311ece96587 and rerun the deterministic contract.

## Remaining work

- Wait for parent operator root refresh.
- Rerun expanded deterministic contract.
- Operator launches frozen PA2 backbone from a clean exact-SHA checkout in DNNs.
- Run Architecture C final evaluator and validate Stage 02 result schema.

## Blockers / gates

- Final target-quarantine source be04a4a4428a3c57233fc1ee598b4311ece96587 is validated in parent authority 0c39bad0219d553fcd1ee8780374412ab9efab46 but not yet installed live.
- No currently accepted connected executor authorizes scientific PyTorch training. PADataset gpu-ci is CI-only; Workspace Shell lacks DNNs/PyTorch.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
