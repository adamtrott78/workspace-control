<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/mth602-final-multisurrogate-dqnguard-v1.json`

## Current Track-A state

Track-A backbone training remains **complete**:

- PADataset PR #26 base evaluator stack: `99ba123e1455566e16d86d6faf67fef3be8ab0b9`
- canonical backbones: **10/10 COMPLETE**
- frozen directional requests: **20/20**
- no additional backbone training is authorized or needed.

The evaluator runtime repair is now stacked in draft PADataset PR #31:

- PR #31 exact head: `b141020bf7b171571879abdf18a836132e80d1d5`
- base: PR #26 exact head `99ba123e1455566e16d86d6faf67fef3be8ab0b9`
- candidate-pytest receipt: `job-0d273d89-0dd0-4f45-96d4-69259e41d87c`
- result: **40 passed**
- no merge authority.

The repair is intentionally narrow:

1. intentional zero-sized **target** validation loaders are treated as absent instead of being concatenated;
2. required known/test/target-test splits remain strict;
3. the surrogate calibration config restores the original L2O semantics:
   - `open_val_frac=0.15`
   - `build_balanced_val_open=true`
   - `require_true_val_open=true`
4. the target config remains quarantined at zero target-open validation.

## Live GPU2 trust

Refresh-v3 is now **LIVE / PASS**:

- predecessor policy: `70f49bf44a638460eb7fe209b1a313740955a25627ff012abf99671b9de5634d`
- active v3 receipt SHA256: `94082c91fabefa2330829197c79acf5f644e78630ae92a6e75264b29cbbe20ab`
- live lane-B policy SHA: `a9c7cb11b0933b5265c9f667c93403e131264f62439660fb0ad8beabf40318be`
- trusted workflow blob: `85e8deef5240e2d6d7db34318e6b2c35947a83f3`
- PADataset main: `dbf167b23e6a1777a31ad5c4bccde44d26d0aad6`

## PA1 -> PA2 acceptance cell

The required acceptance cell is now **fully PASS**.

Final run:

- run: `43975684664`
- job: `133678922111`
- evaluator candidate: `b141020bf7b171571879abdf18a836132e80d1d5`
- result artifact: `14280124476`
- result artifact digest: `sha256:7a031f733917ed5772de720be892e34900cff1d4870aaee2ea3e45effc43af7a`
- GPU UUID: `GPU-cfed3394-a935-63aa-9325-c4cae7b568b6`
- scientific receipt: **PASS**

Frozen backbone provenance:

- source artifact: `14208028365`
- source digest: `sha256:56bc6ba3b124ef2cc042762f7de0f56a0ec19b35986cdffe6a08a6df5a147011`
- source run/job: `43823548277 / 133151929831`
- source candidate: `11338e6c5f9054bd7683658e2ab2fa8ddb5406a5`
- best-model SHA256: `6cad772f2b88e8f768ca8c623112e48b980ce1706e4dc6a1ac40a5c826f690f3`
- config SHA256: `212381aef96580dafe80ba9d36aacdaea8f01283533bf705840aec93168e9aba`
- rehydration recorded `target_test_consumed=false` before final evaluation.

Scientific invariants verified:

- `target_labels_used_for_tuning=false`
- `mix_true_open=false`
- `surrogate_only_open_calibration=true`
- threshold source: `known_only`
- known reject calibration: `0.0512` at declared `0.05` budget
- surrogate-open recall `0.8288` is diagnostic only.

Final PA1 -> PA2 metrics:

- known reject rate: `0.0508148148148148`
- unknown precision: `0.9486872615752862`
- unknown recall: `0.4241380463498646`
- unknown F1: `0.5861989277130708`
- OSR accuracy: `0.587447872266894`
- OSR macro-F1: `0.7151037604271367`
- unknown AUROC: `0.8539393309973854`

Two earlier post-v3 acceptance runs were deterministic code-path failures before a complete result record:
- `43973955075 / 133673000667`: empty optional target `val_open` concatenation.
- `43974924844 / 133676329515`: surrogate config inherited target quarantine `open_val_frac=0`.

Neither failure is evidence for scientific method selection or target-informed retry.

## Immediate next action

Schedule the **remaining 19 frozen Track-A directional evaluator cells** on exact PR #31 head `b141020bf7b171571879abdf18a836132e80d1d5`.

Requirements:

- no backbone retraining;
- no modification of frozen request manifests;
- no target labels for DQN fitting, surrogate selection, threshold selection, HPO, retry decisions, or method selection;
- preserve surrogate-only open calibration and known-only thresholds;
- aggregate the 20-cell matrix only after all cells are terminal and provenance-valid.

## Other lanes

- Track B Architecture B remains separate.
- STFT remains separate and is still gated on repaired PA1 provenance preflight.
- Preserve the first 120 completed STFT overlay records.
- Do not merge PR #31, PR #26, PR #23, PR #21, or unrelated workspace-control branches without separate explicit authority.

## Remaining Track-A matrix queue

All other **19** frozen directional cells were submitted exactly once on PR #31 head `b141020bf7b171571879abdf18a836132e80d1d5` through the trusted GPU2 workflow.

Workflow run numbers are **77-95**, with GitHub run IDs from `43976846146` through `43976937980` (exact per-cell run/job binding is authoritative in the JSON capsule).

Do **not** enqueue duplicates. Current lane A was deliberately left unchanged because its trusted workflow does not authorize `l2o_directional_eval`.

A safe operator-side tmux queue view is:

```bash
tmux new -s mth602-matrix 'watch -n 3 "gh run list -R adamtrott78/PADataset -w lambda-ci-scientific-2.yml -L 25"'
```

Detach with `Ctrl-B D`; reattach with `tmux attach -t mth602-matrix`.
