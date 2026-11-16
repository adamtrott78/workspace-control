<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

## Track-A live state

- Canonical backbone bank: **9/10 COMPLETE**
- Sole remaining training:
  - GPU0: PA3-PA4 — run 43943016274 / job 133565212672
- GPU1 is intentionally idle; there is no additional unique backbone to launch.
- All training remains bound to PADataset PR #24 exact head d1fd5b6d414e7b88675485f576732a424504455f.
- Reverse-direction backbone retraining is forbidden.

## Newly frozen PA3-PA8 result

- SUCCESS run 43943022113 / job 133565235633
- artifact 14267872094
- artifact digest sha256:eb608ed9ccd6c17a8447a27778227435bbc389e48696178cec98933dcc440aa7
- best epoch 1
- best known-val macro-F1 0.8966316187092961
- known-test macro-F1 0.8952296085145685
- early stop epoch 11
- target_test_consumed=false
- target quarantine preserved

## Evaluator candidate

- PADataset PR #26 exact head: 5520601b999c10202457760368f7e13d7bc8a439
- Base: PR #24 exact head d1fd5b6d414e7b88675485f576732a424504455f
- Frozen state: 9 canonical backbones / 18 directed evaluator request manifests
- Includes provenance-safe artifact transport/rehydration, frozen evaluator policy, provenance-bound result records, strict 20-cell aggregation, matrix reporting, and bounded evaluator-operation design
- No workflow-authority file changes
- No merge authority

## Next safe action

Monitor only PA3-PA4. On SUCCESS, freeze its exact workflow/artifact/checkpoint/config provenance into PR #26 and create the final two directional evaluator requests. That completes the 10-backbone / 20-cell Track-A bank.

Then stop backbone training, refresh the Workspace Shell authority snapshot while preserving the pinned live SHAs, validate PR #26 through authorized candidate execution, and only then separately review/activate the bounded directional evaluator workflow operation.

No merges without explicit authority.
