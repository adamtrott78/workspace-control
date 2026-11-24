<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

## Task

- ID: mth602-final-multisurrogate-dqnguard-v1
- Title: MTH 602 final project / PADataset multi-surrogate DQNGuard
- Status: IN_PROGRESS

## Current scientific checkpoint

- Final t007 directional matrix: **20/20 CLOSED**
- Final cell: PA8<-PA3, lane B run `45444347242` / job `138623859746` = SUCCESS
- Result artifact: `14945842346`, digest `sha256:34dac735ef37d788e956c89b91478ca0c0a07a346a789320970d1c52fc69ed01`
- U-F1: `0.9074289030760302`; AUROC: `0.9227523467878138`; known reject: `0.0634320053416425`
- Provenance: scientific receipt PASS; target labels not used for tuning; threshold source known-only

## Lane-A recovery

- Operator authority is explicit.
- Harmless smoke comment: `7139263906`
- Lane-A smoke run/job: `45449088526 / 138640917329`
- Current provider state: queued, unassigned, `runner_id=0`
- This reproduces the lane-A controller stall independently of OSR science.
- Connected Workspace Shell cannot execute the required root restart: reviewed-helper registry is empty and signed approvals cannot be minted by chat.
- GitHub self-hosted Workspace Control runners are intentionally isolated from root control paths.

## Next safe action

Execute exactly:

`sudo systemctl restart workspace-ci-v3-controller@padataset-scientific-single-gpu-v1.service`

Then monitor only smoke run `45449088526` / job `138640917329`. Recovery is accepted only if the smoke acquires a runner and completes SUCCESS. Do not edit controller/root ledgers, restart the provisioner, widen Workspace Shell authority, issue another smoke, or admit science.

## Remaining work

- Prove lane-A recovery with the existing bounded smoke.
- After lane A is healthy, finalize Rule A and retrospective confusion-exclusion correlations/ranking/regret on all 20 cells.
- Then execute frozen historical Rule B confidence-geometry and Rule C feature-geometry replication without CPU overlap.
- Compare historical vs repaired selector behavior and distinguish target-blind deployable metrics from target-aware retrospective mechanism diagnostics.

## Blockers / gates

- Connected root-execution capability only; authority is no longer blocked.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Treat the capsule and exact Git/runtime evidence as authoritative.
Follow the capsule's next_safe_action.
