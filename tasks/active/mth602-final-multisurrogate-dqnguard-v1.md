<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

## Track-A backbone state

- Canonical backbone bank: **9/10 COMPLETE**
- Sole remaining training:
  - GPU0: PA3-PA4 — run 43943016274 / job 133565212672
- GPU1 is idle pending evaluator workflow activation.
- Reverse-direction backbone retraining remains forbidden.

## Workspace Shell / PR #26 validation

- Workspace Shell stale-authority gate: **CLEARED**
- Refresh Tools exposed `candidate-pytest`.
- PR #26 current validated candidate SHA: `15c92fcc7bffe56d6fb29ca5719e9a0f9dd8e766`
- candidate tree: `a384451c831db92834ab3e14e480de806acf5bf4`
- candidate receipt: `job-ef08c200-1c9d-4fc3-a10d-4c9d0a1084a4`
- result: **35 passed**
- durable PADataset checkpoint bound in receipt: `befe383fd67c8bca8d8ce370344b33c7e13cd52f`
- ordinary task-bound execution still rejects the off-checkpoint candidate with `TASK_SHA_MISMATCH`.

PR #26 required a tracked `local_artifacts/evidence/` mountpoint marker because clean Git materializations do not preserve empty directories. This preserves the read-only evidence bind; no Workspace Shell guard was weakened.

## GPU2 directional evaluator workflow candidate

- PADataset draft PR #27
- branch: `mth602-l2o-evaluator-workflow-v1`
- exact head: `613387d22299bbb11481aa38b745be2f2fc29617`
- validation receipt: `job-e81ee184-0f61-40c8-a3e6-42a71bd87ade`
- result: **3 passed**
- diff:
  - new GPU2-only bounded directional evaluator workflow
  - static authority-surface contract test
  - Workspace Shell evidence mountpoint marker
- workflow accepts only frozen request manifests under `manifests/configs/l2o_directional_eval_v1/`
- permissions are read-only: actions / contents / pull requests
- no backbone-training operation exists in the new workflow
- PR #27 is **draft, unmerged, inactive**
- no merge authority has been granted

## Next safe action

A genuine authority gate has been reached.

If explicit merge/activation authority is granted for **PR #27 only**:
1. merge PR #27;
2. verify the exact resulting default-branch workflow SHA;
3. launch one already-frozen PR #26 directional request on GPU2;
4. inspect the complete result artifact and scientific receipt before scheduling more cells.

Separately, continue monitoring PA3-PA4. On SUCCESS, freeze backbone #10 and create its final two directional evaluator requests.

Do not merge PR #26 or any backbone PR without separate explicit authority.
