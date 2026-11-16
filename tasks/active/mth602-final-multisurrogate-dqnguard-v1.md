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

Open a fresh ChatGPT chat with Workspace Shell selected so the refreshed plugin schema exposes `candidate-pytest`. Continue this durable task from PR #640 and validate PADataset PR #26 exact current head through the authorized off-checkpoint candidate path while durable PADataset authority remains pinned at `befe383fd67c8bca8d8ce370344b33c7e13cd52f`.

In parallel, monitor only PA3-PA4. On SUCCESS, freeze its exact workflow/artifact/checkpoint/config provenance into PR #26 and create the final two directional evaluator requests. Do not launch another backbone.

No merges without explicit authority.
