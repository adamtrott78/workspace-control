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

Continue Stage 00 read-only provenance recovery from PADataset@17e1147614f27702e43565089d618182ff71c5af and the untouched historical evidence checkout mounted at local_artifacts/evidence. Start with docs/experiments/multisurrogate_dqnguard/TASK.md, then recover baseline CSV/evaluator/run/config/checkpoint/cache/calibration identities. Do not begin Stage 01 until the provenance gate closes.

## Remaining work

- Read the canonical scientific task and recover fixed-Scan DQNGuard baseline provenance.
- Recover the full 20-cell target-surrogate matrix provenance and VarMax surrogate-all evidence chains.
- Recover baseline CSVs, evaluator summaries, run directories, configs, checkpoints, cache identities, and calibration/evaluator settings.
- Record inaccessible historical subdirectories explicitly if legacy permissions block read-only traversal.
- Persist a machine-readable Stage 00 provenance artifact and update the authoritative PADataset task only after evidence recovery is complete.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
