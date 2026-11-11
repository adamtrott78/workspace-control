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
- Remote checkpoint: 694a0c828ed4c8e8d02a344eb2451905e171aaca
- Remote verified: true

## Next safe action

After operator installs authority f7b8a40f9f50e584974fac92e5eef4773405606b, verify PADataset 694a0c828ed4c8e8d02a344eb2451905e171aaca and run the expanded deterministic contract test.

## Remaining work

- Wait for parent operator root refresh.
- Run expanded tests/test_multisurrogate_dqnguard.py through research-bounded.
- Train manifests/configs/mth602_stage03/archC_backbone_knownonly_unkPA2_c16384_seed0.json.
- Run Architecture C small-real evaluator and validate Stage 02 result schema.

## Blockers / gates

- Backbone-ready source 694a0c828ed4c8e8d02a344eb2451905e171aaca is validated in parent authority f7b8a40f9f50e584974fac92e5eef4773405606b but not yet installed live.
- Scientific GPU execution requires the DNNs PyTorch environment; Workspace Shell will first validate the expanded deterministic contract after the root refresh.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
