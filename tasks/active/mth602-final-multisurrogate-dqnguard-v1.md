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
- Remote checkpoint: 17e1147614f27702e43565089d618182ff71c5af
- Remote verified: true

## Next safe action

Finish and live-validate workspace-shell-multirepo-research-v1. Then call Workspace Shell against target PADataset with expected SHA 17e1147614f27702e43565089d618182ff71c5af and begin Stage 00 read-only provenance recovery.

## Remaining work

- Complete and deploy workspace-shell-multirepo-research-v1.
- Use Workspace Shell to establish PADataset branch, HEAD, and status read-only.
- Recover baseline CSVs, evaluator summaries, run directories, configs, checkpoints, cache identities, and calibration/evaluator settings.
- Persist machine-readable Stage 00 provenance in PADataset and update its authoritative task.
- Proceed to Stage 01 only after the provenance gate closes.

## Blockers / gates

- Workspace Shell live runtime does not yet expose the PADataset target; workspace-shell-multirepo-research-v1 is implementing and validating that capability.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
