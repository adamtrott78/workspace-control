<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

## Track-A live state

- Status: IN_PROGRESS
- Canonical backbone bank: **8/10 COMPLETE**
- Final two live trainings:
  - GPU0: PA3-PA4 — run 43943016274 / job 133565212672
  - GPU1: PA3-PA8 — run 43943022113 / job 133565235633
- Both are bound to PADataset PR #24 exact head d1fd5b6d414e7b88675485f576732a424504455f.
- After these two, no additional backbone training is permitted; reverse directions are evaluator-only reuse.

## Newly frozen results

PA2-PA8:
- SUCCESS run 43926895324 / job 133508635811
- best epoch 2
- best known-val macro-F1 0.9433003897151243
- known-test macro-F1 0.9448806320168245
- target_test_consumed=false
- artifact 14258984518
- target quarantine preserved

PA2-PA3:
- SUCCESS run 43921420197 / job 133489412741
- best epoch 3
- best known-val macro-F1 0.9253955249097198
- known-test macro-F1 0.9195729464289638
- target_test_consumed=false
- artifact 14259500161
- target quarantine preserved

## Evaluator candidate

- PADataset PR #26 exact head: 0a4a6d194320ba72bd5b874806aba54d45a6f4f7
- Base: PR #24 exact head d1fd5b6d414e7b88675485f576732a424504455f
- Current frozen evaluator state: 8 canonical backbones / 16 directed request manifests
- No workflow-authority file changes
- No merge authority

## Workspace Shell gate

Authoritative candidate pytest remains fail-closed because the live Workspace Shell authority snapshot still sees the older CHECKPOINTED task state.

Preserve:
- workspace-control live execution: 5401045341090a26a42ce3a497c379f8223a3b54
- PADataset authority: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- recorded dependency generation: 4469009659182c8c2f4d12d727e556f2a2995fc9

## Next safe action

Wait for the two final canonical backbone runs above. On each SUCCESS, freeze exact artifact/checkpoint/config provenance into PR #26 and create its two directional evaluator requests. Then stop backbone training, refresh Workspace Shell authority without rebinding the preserved SHAs, validate PR #26, and only then authorize/run the frozen 20-cell directional evaluator matrix.

No merges without explicit authority.
