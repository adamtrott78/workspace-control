<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-final-multisurrogate-dqnguard-v1
- Title: MTH 602 final project / PADataset multi-surrogate DQNGuard
- Status: IN_PROGRESS
- Current stage: tracka_l2o_control_repair
- Capsule schema: v2

## Track-A live state

- Canonical reduction: 20 directed target/surrogate cells -> 10 unique unordered excluded-pair backbone trainings.
- Completed and provenance-frozen: 6/10.
- Completed: PA1-PA2, PA1-PA3, PA1-PA4, PA1-PA8, PA2-PA4, PA4-PA8.
- GPU0 live: PA2-PA8, run 43926895324 / job 133508635811.
- GPU1 live: PA2-PA3, run 43921420197 / job 133489412741.
- Remaining after those two: PA3-PA4 and PA3-PA8.
- Reverse-direction backbone retraining is forbidden; evaluator direction remains ordered.
- Target labels remain forbidden for fitting, HPO, threshold selection, retry decisions, or method selection.

## Exact candidate stack

- Runtime-only w4 training candidate: PADataset PR #24 @ d1fd5b6d414e7b88675485f576732a424504455f.
- Directional evaluator/artifact candidate: PADataset PR #26 @ 29e333ce4d036548ab6e6045ad7bea0ac234a4aa, stacked on exact PR #24 head.
- PR #26 contains:
  - canonical 10-backbone / 20-directed-cell matrix,
  - frozen Track-A evaluator policy,
  - per-direction immutable request manifests for completed backbones,
  - GitHub artifact ID/digest/workflow-run binding,
  - ZIP/checkpoint/config provenance-safe rehydration,
  - directional reuse and target-quarantine contracts/tests.
- Actual PR #26 branch-data validation: 10 canonical backbones, 20 directed cells, 6 complete, 4 remaining, 12 frozen requests, zero invariant errors.
- No workflow authority changes and no merge authority are implied.

## Latest completed backbone

PA1-PA3 run 43900286950 / job 133414700376:
- SUCCESS.
- best epoch 26.
- best known-validation macro-F1 0.999925851719.
- known-test macro-F1 0.9998517364899926.
- early stop epoch 36.
- target_test_consumed=false.
- target quarantine preserved.
- validation showed large intermittent collapses despite smooth training loss; the known-only best-checkpoint rule correctly preserved epoch 26.

## Workspace Shell gate

Authoritative candidate pytest is still fail-closed because the live Workspace Shell authority snapshot sees the older CHECKPOINTED MTH602 capsule.

Do not weaken or bypass that guard.

Required authority preservation during refresh:
- live workspace-control execution snapshot: 5401045341090a26a42ce3a497c379f8223a3b54
- live PADataset authority: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- recorded MTH602 workspace-control dependency generation: 4469009659182c8c2f4d12d727e556f2a2995fc9

## Next safe action

Keep both scientific GPU lanes saturated only with the remaining unique Track-A canonical backbones bound to exact PR #24 head d1fd5b6d414e7b88675485f576732a424504455f.

On each SUCCESS:
1. freeze workflow run/job, artifact ID/digest, candidate SHA, best_model SHA, config SHA, metrics, early-stop epoch, and target-quarantine evidence into PR #26;
2. create the two immutable directional evaluator request manifests;
3. never train the reverse direction.

After the 10-backbone bank is complete:
- refresh Workspace Shell authority without rebinding the pinned live SHAs above;
- validate PR #26 through authorized candidate execution;
- only then add/review the bounded artifact-download + directional evaluator operation in the authority-owned scientific workflow;
- run the frozen 20-cell Track-A matrix.

Track B Architecture B and the STFT diagnostic remain preserved under their existing gates.

## No-merge rule

Do not merge PADataset PRs #17, #21, #22, #23, #24, #25, #26 or workspace-control PRs #636, #637, #640 without explicit merge authority.
