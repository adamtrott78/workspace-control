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

- **PASS / RECOVERED**
- Operator executed exactly:
  `sudo systemctl restart workspace-ci-v3-controller@padataset-scientific-single-gpu-v1.service`
- Acceptance smoke: run `45449088526` / job `138640917329`
- Smoke conclusion: **SUCCESS**
- Runner: `lambda-padataset-scientific-single-gpu-26c92d91f498`
- Smoke artifact: `14949111150`
- Artifact SHA256: `092167500e6f6c8fe5c6f8b91a854eff476bb495dd3ade5a76d0407db07c9303`
- No ledger edits, provisioner restart, policy change, duplicate smoke, or science admission occurred.

## Next safe action

Finalize Rule A guard-score and retrospective target-aware confusion-exclusion analysis on all 20 frozen post-hoc cells. Do not feed selector evidence back into backbone/checkpoint/threshold selection.

## Remaining work

- Prove lane-A recovery with the existing bounded smoke.
- After lane A is healthy, finalize Rule A and retrospective confusion-exclusion correlations/ranking/regret on all 20 cells.
- Then execute frozen historical Rule B confidence-geometry and Rule C feature-geometry replication without CPU overlap.
- Compare historical vs repaired selector behavior and distinguish target-blind deployable metrics from target-aware retrospective mechanism diagnostics.

## Blockers / gates

- None for lane-A recovery; gate closed.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Treat the capsule and exact Git/runtime evidence as authoritative.
Follow the capsule's next_safe_action.
