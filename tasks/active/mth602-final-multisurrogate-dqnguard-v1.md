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

After the parent live upgrade reports LOCAL_TASK_AUTHORITY=PASS, verify this task through ChatGPT Workspace Shell and verify PADataset exact HEAD 17e1147614f27702e43565089d618182ff71c5af. Only then begin Stage 00 read-only provenance recovery from the clean execution snapshot and untouched historical evidence checkout leaf2026-review-1571342865@b5a09cede6680b9e2a53eac244db4fbd7eaf76ec.

## Remaining work

- Apply the validated parent authority refresh and prove this task is visible through Workspace Shell.
- Verify clean PADataset execution HEAD is 17e1147614f27702e43565089d618182ff71c5af and historical evidence is mounted read-only.
- Recover baseline CSVs, evaluator summaries, run directories, configs, checkpoints, cache identities, and calibration/evaluator settings.
- Persist machine-readable Stage 00 provenance in PADataset and update its authoritative task.
- Proceed to Stage 01 only after the provenance gate closes.

## Blockers / gates

- Parent Workspace Shell implementation is validated at execution candidate 1a9a24fc1bc6e5cda2984e296151a378138600c8, but this task still returns TASK_NOT_FOUND through the live trusted authority snapshot. No PADataset read or research execution is permitted until the authority refresh completes.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
