<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

## Track-A backbone state

- Canonical backbone bank: **9/10 COMPLETE**
- Sole remaining training: GPU0 PA3-PA4 — run 43943016274 / job 133565212672
- GPU0 run remains IN_PROGRESS.
- Reverse-direction backbone retraining remains forbidden.

## PR #26 evaluator validation

- Workspace Shell `candidate-pytest` available after Refresh Tools.
- PR #26 validated candidate SHA: `15c92fcc7bffe56d6fb29ca5719e9a0f9dd8e766`
- candidate tree: `a384451c831db92834ab3e14e480de806acf5bf4`
- receipt: `job-ef08c200-1c9d-4fc3-a10d-4c9d0a1084a4`
- **35 passed**
- durable PADataset checkpoint in receipt: `befe383fd67c8bca8d8ce370344b33c7e13cd52f`
- ordinary task-bound execution rejects the off-checkpoint candidate with `TASK_SHA_MISMATCH`.

## PR #27 merge / activation attempt

Explicit authority was granted to merge and activate PR #27 only.

- PR #27 head: `613387d22299bbb11481aa38b745be2f2fc29617`
- merged successfully to PADataset main: `7782be95f409dc7bccf2729915e4014c0178428c`
- evaluator workflow blob: `ba825a98f0aa49bbdc78f5ed37faaf33c1982b4a`
- first frozen acceptance cell: PA1 -> PA2
- evaluator run: `43963122999`
- evaluator job: `133635479325`
- status: **QUEUED**
- trusted lane-B smoke run: `43963420422`
- trusted lane-B smoke job: `133636487691`
- status: **QUEUED**
- shared provisioner: active/running

## Live control-plane blocker

Lane B remains bound to exactly one trusted workflow:

- path: `.github/workflows/lambda-ci-scientific-2.yml`
- blob: `6280a6e7b2ad8cc379277fa320e8839a94f360ec`

The newly merged evaluator workflow is a different path/blob and therefore is not authorized by the live lane-B controller. The reviewed Workspace Shell helper registry contains no lane-B workflow-refresh helper.

No controller trust was widened and no privileged authority was invented.

## Next safe action

A separate reviewed lane-B trusted-workflow refresh path is required.

Preferred correction:
1. extend the existing trusted `.github/workflows/lambda-ci-scientific-2.yml` with the bounded `l2o_directional_eval` operation;
2. validate the exact candidate;
3. refresh lane-B's trusted workflow blob through a reviewed, one-shot root/operator authority path;
4. launch one frozen cell and verify its scientific receipt before scheduling further cells.

Do not mutate live lane-B controller trust without separate explicit authority.
