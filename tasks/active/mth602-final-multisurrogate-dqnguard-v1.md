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

Wait for the parent workspace-shell-multirepo-research-v1 authority refresh to validate and deploy. Then verify this task through the live Workspace Shell task gate and begin Stage 00 using clean PADataset execution source 17e1147614f27702e43565089d618182ff71c5af plus the untouched historical evidence checkout leaf2026-review-1571342865@b5a09cede6680b9e2a53eac244db4fbd7eaf76ec.

## Remaining work

- Complete exact-head validation and live authority refresh under workspace-shell-multirepo-research-v1.
- Verify this task is visible through Workspace Shell and clean PADataset execution HEAD is 17e1147614f27702e43565089d618182ff71c5af.
- Recover baseline CSVs, evaluator summaries, run directories, configs, checkpoints, cache identities, and calibration/evaluator settings from the read-only historical evidence mount.
- Persist machine-readable Stage 00 provenance in PADataset and update its authoritative task.
- Proceed to Stage 01 only after the provenance gate closes.

## Blockers / gates

- Workspace Shell schema now exposes PADataset and research-bounded, but this task is not yet visible through the live trusted authority snapshot: live inspection returns TASK_NOT_FOUND. Parent candidate ce19452c644599bda23f6e3766c9390fa0d906db repairs independent authority refresh; no PADataset execution is permitted until that gate passes.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
