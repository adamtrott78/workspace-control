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


## GPU0 evaluator scale-out candidate

GPU0 support is now engineered and candidate-validated, but **not live yet**.

- PADataset draft PR #32
- exact head: `e77c82d90b36d6223877909adf2d5d0a490c3beb`
- lane A remains `ci-padataset` / `lambda-padataset-scientific-single-gpu` / GPU0 `GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea`
- candidate-pytest receipt: `job-7cead1f2-3c5e-4a7d-b870-672c09c52086`
- result: **14 passed**
- PR remains OPEN/DRAFT/UNMERGED; no merge authority has been inferred.

The candidate ports the already-accepted GPU2 bounded `l2o_directional_eval` path to GPU0 without changing frozen request, provenance, target-quarantine, surrogate-calibration, or known-only-threshold semantics.

Current authority gate: explicit permission is required to merge PR #32. After merge, a new default-branch workflow blob/main SHA must be bound into a chained lane-A trusted-workflow refresh and activated under fresh root/operator authority before any `/lambda-scientific ... l2o_directional_eval:...` request can be admitted on GPU0.

Do not cancel GPU2 queued cells until GPU0 trust is live. At this checkpoint run 77 is SUCCESS, run 78 is IN_PROGRESS, and runs 79-95 are still queued.


## Track-A complete matrix — 2026-11-17

All 20 frozen directional Track-A cells are now terminal **SUCCESS/PASS**. Acceptance run 43975684664 plus workflow runs #77-#95 completed on the trusted GPU2 lane at evaluator head `b141020bf7b171571879abdf18a836132e80d1d5`.

Every result preserves:
- `target_labels_used_for_tuning=false`
- `surrogate_only_open_calibration=true`
- `threshold_source=known_only`
- `mix_true_open=false`

Unknown-F1 matrix:

| target \ surrogate | PA1 | PA2 | PA3 | PA4 | PA8 |
|---|---:|---:|---:|---:|---:|
| PA1 | — | 0.586199 | 0.616065 | 0.241099 | 0.254204 |
| PA2 | 0.899485 | — | 0.027741 | 0.130573 | 0.801033 |
| PA3 | 0.984317 | 0.001426 | — | 0.961990 | 0.054209 |
| PA4 | 0.858484 | 0.310583 | 0.439280 | — | 0.491409 |
| PA8 | 0.936550 | 0.757011 | 0.424513 | 0.860657 | — |

Paper comparison: **17/20 cells improved, 3/20 declined**. Mean unknown-F1 changed from **0.4115** to **0.531841** (+0.120341 absolute, +29.2% relative). The only large regression is PA1<-PA4 (0.71 -> 0.241099); the other two declines are small: PA2<-PA4 (0.15 -> 0.130573) and PA8<-PA2 (0.77 -> 0.757011).

Best frozen surrogate by target: PA1<-PA3, PA2<-PA1, PA3<-PA1, PA4<-PA1, PA8<-PA1. PA1/Scan is therefore the best eligible surrogate for all four other targets.

This comparison is descriptive only. Do not use target-test metrics for retries, method selection, or Track-A tuning.

GPU0 evaluator PR #32 is no longer required for Track-A completion because the full matrix finished on GPU2; it remains draft/unmerged absent separate infrastructure authority.


## Track-B Architecture B B0 gate — 2026-11-17

Workspace Shell evidence-mount repair is now live:

- authority snapshot: `29ba42ffde725c16f5cfc70b3c47ecfd76d2511d`
- runtime: `f3f999ff0200e2450d83e93887b2450f1ee83e2f`
- PADataset execution authority: `befe383fd67c8bca8d8ce370344b33c7e13cd52f`
- `WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS`
- semantic acceptance receipt: `job-2a411e27-5c65-44b8-8ada-362dd7b90769`
- evaluator isolation receipt: `job-9ed9aed7-d545-4929-9405-d5782788e461`

Architecture-B implementation candidate is draft PADataset PR #23, exact head:

`82790f9c07d5eb9ea48b37be026672c0a1f7fad8`

Candidate validation:
- lightweight logic suite: 4 passed;
- target-consumption ordering suite: 5 passed;
- frozen B0 request + artifact transport/rehydration contract: **10 passed** at receipt `job-775e5e03-0239-4786-ba94-16fbaa2a09a7`.

Important repair: the evaluator previously materialized `test_open` before `method.fit()`. It now builds only `val_known` + `test_known`, freezes the Architecture-B winner, and only then materializes PA2 target-open. Thus the claim `target_first_consumed_after_winner_frozen=true` is now behaviorally true rather than metadata-only.

B0 source backbone is frozen to:
- artifact: `14180249360`
- workflow run: `43751609944`
- artifact digest: `sha256:f7de2637df85487b21903a448630815fc63c1247253b98ffc754b46586b9b39b`
- config SHA256: `a9c08353490f944ec1c5fb363002f41a8b32f875914251c30604cc2c03b35188`
- best-model SHA256: `4fa0c67d1c0c619ab4cde058519ca603fa95d8afb8f58ebf8d564ebafb9989ef`
- target PA2 remained quarantined: `target_test_consumed=false`.

Draft PADataset PR #33, exact head `04edac624853ea9e8bb48e09f9240e086fcc2b69`, adds exactly one bounded GPU2 workflow opcode: `archb_cross_surrogate`. Static trust tests passed 2/2 at receipt `job-ceb52813-d732-4f6c-903f-c1bbd503f458`.

**Current gate:** PR #33 is OPEN/DRAFT/UNMERGED. The live lane-B workflow therefore does not yet authorize B0. Explicit merge authority is required. After merge, the exact new main SHA/workflow blob must be bound into a fresh trusted-workflow refresh before any B0 job is submitted.


## Architecture-B lane-B trust merge and refresh-v4 gate

Explicit authority `MERGE PR 33` was consumed only for PADataset PR #33.

PR #33 was marked ready-for-review (GitHub cannot merge drafts) and merged at its exact validated head:

- PR #33 head: `04edac624853ea9e8bb48e09f9240e086fcc2b69`
- merge commit / new PADataset `main`: `6a3c17c27a401f059f9ded1287d274d766f61283`
- new `.github/workflows/lambda-ci-scientific-2.yml` blob: `650a529aeee51b53234a84b3afea8743cc527688`
- live predecessor blob remains `85e8deef5240e2d6d7db34318e6b2c35947a83f3` until root activation.

Workspace Control draft PR #643 now implements a **v3 -> v4** one-shot lane-B trusted-workflow refresh:

- exact candidate head: `ef43b5352cf4c3e799a09ff917878b6e32ef1882`
- requires refresh-v3 active receipt as exact predecessor;
- preserves all older receipts;
- requires zero assigned/running/active workflow work;
- changes only the lane-B controller policy/workflow blob;
- consumes fresh operator authority with O_EXCL;
- rollback target is refresh-v3.

Validation:
- `job-676fbcf1-4593-484c-87bb-92ae8247dccd`: **16 passed** (v3+v4 focused);
- `job-d67324a2-5b28-492b-ab17-dd62615b20d5`: **37 passed** (full dual-lane + refresh v1/v2/v3/v4 stack).

**Current gate:** root/operator activation of refresh-v4. Do not launch Architecture-B B0 until `PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4=PASS` and postverification confirm blob `650a529a...` is live.


## Current checkpoint — Architecture-B B3 terminal PASS

This section supersedes the older B3-live checkpoint. The authoritative source remains the JSON capsule.

### Architecture-B B3 final state

Initial run #100 / `44176896203` failed only during final result-record assembly because B3 threshold calibration is keyed by the composite candidate ID while the result record indexed it with the bare surrogate. The retry decision was made from the exception/code path only; no PA2 metric from the failed artifact was inspected or used.

Minimal repair:

- PADataset PR #23 repaired exact head: `0ea0d2aa655a943e921918500f72b987e79922c3`
- frozen B3 request blob remained unchanged: `d2894a9ebc4c13e6e3fa8821de9707f089ddd8aa`
- candidate-pytest receipt: `job-2b0f1b05-f54c-46e0-a675-74716b9726a3`
- result: **27 passed**
- PR #23 remains **OPEN / DRAFT / UNMERGED**

Exactly one repair retry was admitted:

- comment: `6961561824`
- workflow run: **#101**
- run ID: `44180560029`
- job ID: `134383439162`
- result: **SUCCESS**
- artifact: `14372803489`
- artifact digest: `sha256:c72fe383cdfd03ffb96eb3dda632ff1f27325066e109542e9a2209ff383423ea`

Artifact validation:

- scientific receipt: **PASS**
- all 10 receipt-listed files matched recorded SHA-256 and byte counts
- source backbone: artifact `14180249360`, workflow `43751609944`
- source artifact digest: `sha256:f7de2637df85487b21903a448630815fc63c1247253b98ffc754b46586b9b39b`
- source candidate: `befe383fd67c8bca8d8ce370344b33c7e13cd52f`
- config SHA256: `a9c08353490f944ec1c5fb363002f41a8b32f875914251c30604cc2c03b35188`
- best-model SHA256: `4fa0c67d1c0c619ab4cde058519ca603fa95d8afb8f58ebf8d564ebafb9989ef`
- rehydration records `target_test_consumed=false`
- fit / guard / norm / threshold / pseudo-open partitions are disjoint
- target labels used for fitting / thresholding / candidate selection: **false**
- target first consumed only after winner freeze: **true**
- threshold source: `known_only`, budget `0.05`

Frozen B3 winner:

- candidate ID: `PA3|gap_variance_equal|scale=2`
- selected surrogate: `PA3`
- band-weight rule: `gap_variance_equal`
- guard scale: `2.0`
- worst off-diagonal unknown-F1: `0.005429864253393665`
- mean off-diagonal unknown-F1: `0.11839836393428993`
- mean off-diagonal OSR macro-F1: `0.7355659549704705`
- known-guard reject: `0.05615790936891854`
- known-only threshold: `3.960840878607268`
- threshold calibration reject: `0.05004170141784821`

The selected candidate's development evidence contains only PA1, PA4, and PA8 off-diagonal pseudo-open rows. Independent recomputation across all 96 bounded B3 candidates selected the same winner.

Descriptive-only PA2 metrics:

- known reject: `0.0563215834537974`
- unknown precision: `0.7494434825624536`
- unknown recall: `0.10118550676239772`
- unknown F1: `0.17829822290220076`
- OSR macro-F1: `0.6602341672942684`
- unknown AUROC: `0.8637250281879134`

These PA2 metrics are final descriptive evidence only. They must not trigger retries, tuning, or method selection.

### Immediate next action

Architecture-B B3 is terminal; do not submit another B3 job.

Return to the separate STFT representation diagnostic. First verify the repaired PA1 provenance preflight against the persistent exact-SHA checkout. **Do not restart STFT blindly. Preserve the first 120 completed overlay records.**

No merge authority is implied for PADataset PR #23, STFT PR #21, or unrelated branches.

### Current STFT gate — local/operator-only

Read-only connected checks confirm the remaining STFT preflight cannot be executed through the current bounded Workspace Shell surface:

- PR #21 exact head: `fd15238aa369118e61b21ab714900861dbb99d2c`
- PR state: **OPEN / DRAFT / UNMERGED**
- Lambda CPU canary: `43788103594` **SUCCESS**
- Workspace Shell candidate attempt: `job-6405de5a-fbc9-4ff7-92ee-3fc90a3758c1`; sandbox lacks `h5py`, so no live-data preflight ran and no STFT/data mutation occurred
- durable PR #21 execution evidence states raw OTA + legacy-cache materialization are intentionally outside connected CI/Workspace Shell authority
- first 120 completed overlay records remain authoritative and must be skipped, not rebuilt

Smallest next operator action:

```bash
EXPECTED_SHA=fd15238aa369118e61b21ab714900861dbb99d2c \
CHECKOUT="$HOME/adamArchives/worktrees/PADataset-stft-track-ablation-v1" \
bash <(curl -fsSL "https://raw.githubusercontent.com/adamtrott78/PADataset/fd15238aa369118e61b21ab714900861dbb99d2c/scripts/mth602/bootstrap_stft_track_ablation_persistent.sh")
```

The bootstrap itself verifies the exact SHA, refuses transient `/tmp` execution for the actual STFT run, performs the real PA1 provenance probe before the long build, and resumes existing output files. Continue only if the live probe resolves a real PA1 legacy base cache and all preflight checks PASS.

### STFT retry gate — exact-checkout import repair

The first local preflight at `fd15238aa369118e61b21ab714900861dbb99d2c` failed **before any cache mutation or GPU work**:

- persistent checkout was correct;
- environment preflight imported `experiments` from the canonical repo current working directory;
- stdin Python places current working directory ahead of `PYTHONPATH`, so the exact detached checkout was shadowed;
- no PA1 provenance decision, overlay build, or training occurred.

Repair:

- PR #21 exact head: `5146d718006e38c6d9110e158c80dfa43b86e882`
- launcher now `cd "$ROOT"` after the persistent-/tmp guard and before preflight imports
- candidate-pytest: `job-732c8e5b-8118-4ddb-88b8-b3a8f72208aa` — **2 passed**
- CPU canary: run `44190444960`, job `134418111372` — **SUCCESS**
- PR #21 remains **OPEN / DRAFT / UNMERGED**
- first 120 completed overlays remain preserved

Rerun only this exact repaired head:

```bash
EXPECTED_SHA=5146d718006e38c6d9110e158c80dfa43b86e882 \
CHECKOUT="$HOME/adamArchives/worktrees/PADataset-stft-track-ablation-v1" \
bash <(curl -fsSL "https://raw.githubusercontent.com/adamtrott78/PADataset/5146d718006e38c6d9110e158c80dfa43b86e882/scripts/mth602/bootstrap_stft_track_ablation_persistent.sh")
```

Continue only if the live PA1 provenance probe resolves a real legacy base cache and all preflight checks PASS. Do not reuse `fd15238...`, do not run from `/tmp`, and do not delete or rebuild the first 120 overlays.

### STFT record-121 provenance repair

The local retry at `5146d718006e38c6d9110e158c80dfa43b86e882` cleared the real environment/provenance gate:

- environment + raw OTA access PASS;
- GPU/CPU STFT transform check PASS;
- real PA1 legacy base cache resolved;
- trajectory and legacy-provenance tests PASS;
- records 1–120 were preserved and skipped.

The run then failed before building record 121 because historical raw source `ota_pa1_run01__shard_001__PA1.mat` could not be resolved by exact path, realpath, or protocol+basename. This older cache lineage can omit `protocol_name`.

Repair head: `122f5d21e648498b4afaa6b857b69f39dbb18222`

- keep exact path -> realpath -> protocol+basename precedence;
- add basename fallback only when exactly one cache file matches across all indexed roots;
- ambiguity remains a hard failure;
- `--probe-only` now resolves all 375 discovered source records before Phase 1 and reports `provenance_records_resolved`;
- functional h5py regressions cover unique-basename success and ambiguity failure;
- Workspace Shell static contract: `job-708219d4-46f9-4dd6-9ec1-70a36e99bbcb` — **3 passed**;
- CPU canary run `44235462841` / job `134570401465` — **SUCCESS**;
- PR #21 remains **OPEN / DRAFT / UNMERGED**.

Run only this exact head:

```bash
EXPECTED_SHA=122f5d21e648498b4afaa6b857b69f39dbb18222 \
CHECKOUT="$HOME/adamArchives/worktrees/PADataset-stft-track-ablation-v1" \
bash <(curl -fsSL "https://raw.githubusercontent.com/adamtrott78/PADataset/122f5d21e648498b4afaa6b857b69f39dbb18222/scripts/mth602/bootstrap_stft_track_ablation_persistent.sh")
```

Accept Phase 1 only after the probe reports `provenance_records_resolved=375`. Preserve/skip the first 120 overlays; do not use `--force`, do not run from `/tmp`, and do not widen Workspace Shell authority.

### STFT canonical source-universe repair

The local retry at `122f5d21e648498b4afaa6b857b69f39dbb18222` failed **before Phase 1** in the new all-source preflight on `ota_pa1_run01__shard_001__PA1.mat`.

Repository production history establishes that this file is not part of the frozen unified-core experiment corpus:

- final cache source is one `ota_core_high_run01` bank root;
- each of 20 shards contributes exactly PA1 part 1, PA1 part 2, PA2, PA3, PA4, PA8;
- all three protocols are included;
- canonical source universe is therefore **3 × 20 × 6 = 360 records**.

Generic directory discovery saw 375 files because 15 dedicated `ota_pa1_run01` artifacts are co-located in those directories. They must not be remapped into the core cache.

Correct repair head: `a5cbd0d2a9e8e287d0288498735e5a4221ed3683`

- freeze STFT source selection to the documented 360 canonical unified-core files;
- fail closed on any missing canonical file;
- count/ignore noncanonical extras;
- restore strict exact source_path -> realpath -> protocol+basename provenance resolution; no basename-only fallback;
- resolve all 360 canonical records before Phase 1;
- preserve/skip the first 120 existing overlays;
- Workspace Shell static contract `job-7a3c08ba-7511-403b-b898-576e1bd6bc3f`: **3 passed**;
- CPU canary run `44236003500` / job `134572181770`: **SUCCESS**;
- PR #21 remains **OPEN / DRAFT / UNMERGED**.

Run only this exact head:

```bash
EXPECTED_SHA=a5cbd0d2a9e8e287d0288498735e5a4221ed3683 \
CHECKOUT="$HOME/adamArchives/worktrees/PADataset-stft-track-ablation-v1" \
bash <(curl -fsSL "https://raw.githubusercontent.com/adamtrott78/PADataset/a5cbd0d2a9e8e287d0288498735e5a4221ed3683/scripts/mth602/bootstrap_stft_track_ablation_persistent.sh")
```

Accept Phase 1 only when the probe reports `canonical_source_records=360` and `provenance_records_resolved=360`. Do not use `--force`, do not run from `/tmp`, and do not delete/rebuild the first 120 overlays.

### STFT terminal PASS and synthesis handoff

The exact persistent STFT run at `a5cbd0d2a9e8e287d0288498735e5a4221ed3683` is terminal **PASS**.

Execution evidence:
- driver `exit_code=0`, `success=true`;
- diagnostic exit code `0`;
- training exit code `0`;
- cache manifest `source_records=360`, `files_skipped=120`, `files_built=240`, `samples_built=99848`;
- first 120 overlay records were preserved and the remaining 240 were built;
- training early-stopped at epoch 17 with best epoch 7; known validation accuracy and macro-F1 were both 1.0;
- PA1/PA4 trajectory diagnostic used 59,903 samples across 180 groups and achieved mean accuracy `0.9996493848663203`, mean macro-F1 `0.9996493838114462`, mean AUROC `0.9999995428914733`;
- strongest single trajectory metrics include mean absolute step bins AUROC `0.9908634178287573`, unique states `0.9892150330513103`, revisit fraction `0.9428091345349965`, and monotonic fraction `0.823980670835702`.

Scientific interpretation: the PA1↔PA4 failure mode is strongly consistent with a representation issue. Their temporal/frequency trajectories are almost perfectly separable once ordering-sensitive STFT-derived trajectory information is exposed, while a global FFT can obscure that ordering.

No additional STFT tuning/retry is justified.

### Current stage

`final_scientific_synthesis`

Next action:
- synthesize Track A, Architecture B, and STFT findings into the final MTH602 result narrative;
- do **not** launch another STFT or B3 job;
- treat the unfinished detv2 seed2 replicate as optional unless the synthesis identifies a specific fixed-partition/split-sensitivity question that actually requires it;
- preserve true-target quarantine and descriptive-only treatment of final target metrics.

### Expanded scientific validation — reopened after STFT terminal PASS

The prior transition directly to final synthesis was premature.

#### 1. STFT representation question remains open at the OSR level

The completed `stft_tracks64_v1` run did train a backbone where the two legacy FFT real/imag channels were replaced with STFT-derived centroid/spread tracks while preserving the eight-channel interface. It also showed that PA1 versus PA4 trajectory features are nearly perfectly separable.

However, this did **not** run a matched DQNGuard OSR comparison against the legacy FFT representation. The representation diagnostic therefore establishes information availability/mechanism, not end-to-end OSR improvement.

Required next experiment: matched FFT vs STFT DQNGuard evaluation, beginning with the PA1-PA4 canonical pair (both directions) under identical partitions/training/evaluator semantics. The STFT choice is post-hoc/exploratory for this pair because PA1/PA4 labels were already used in the trajectory diagnostic.

#### 2. Track-A backbone qualification is incomplete

The frozen repair protocol states a competency gate of known-validation macro-F1 >= 0.95 and minimum known-class F1 >= 0.90, with known-only HPO required for failures.

At least three canonical pairs fail the macro gate:
- PA2-PA3: selected val macro-F1 ~0.9254; known-test macro-F1 0.9195729464;
- PA2-PA8: selected val macro-F1 ~0.9433; known-test macro-F1 0.9448806320;
- PA3-PA8: selected val macro-F1 ~0.8966; known-test macro-F1 0.8952296085.

Therefore the current repaired matrix is a major improvement over the paper's one-epoch matrix, but it is not yet the fully competency-qualified/tuned matrix described by the protocol. Audit min-class F1 for all ten backbones and perform bounded known-only HPO where required.

#### 3. Backbone quality does not explain the matrix change

Across all 20 repaired directional cells, canonical known-test macro-F1 versus repaired unknown-F1 is only moderately related (Pearson r ~0.461; Spearman rho ~0.267).

Averaging both directions per canonical backbone gives Pearson r ~0.585 but Spearman rho ~0.019, showing a non-monotonic relationship dominated by the few low-quality backbones and heavy ceiling effects.

Using the presentation's displayed two-decimal historical matrix, known-test macro-F1 versus the improvement in unknown-F1 is approximately Pearson r ~0.110 and Spearman rho ~-0.032 at the directional-cell level. Thus the large change from the paper matrix is not simply explained by higher final closed-set macro-F1.

#### 4. Re-test the original three target-blind surrogate rules

The paper/presentation evaluated:
- Rule A: surrogate calibration-open recall at the known-only threshold;
- Rule B: confidence geometry using P1, P1-P2 gap, and entropy;
- Rule C: feature geometry using nearest-known-centroid distance / centroid-margin statistics.

Historical outcome: Rule A had essentially zero correlation and picked 2/5 best surrogates; Rule B pointed in the wrong direction; Rule C was the strongest simple positive signal but picked only 1/5.

These must be rerun on the competency-qualified matrix before concluding that simple surrogate selection fails under properly trained backbones. Freeze formulas before inspecting the new target-open outcomes.

#### 5. Replication policy

Do not spend a 10-seed budget until backbone recipe, representation, DQNGuard variant, and selector rules are frozen.

For rigorous variance attribution:
1. fix data partitions and run 10 independent model/training seeds for the final recipe;
2. separately evaluate partition sensitivity using explicit partition seeds (for example several partition seeds with multiple model seeds each);
3. do not use one overloaded `seed` variable that simultaneously changes splits, loader order, and initialization.

Final synthesis resumes only after these expanded validation stages are resolved or explicitly scoped out.

## Research Program v2 — authoritative 2026-11-18 interview freeze

The experimental program is **not** at final synthesis. The operator selected a rigorous MTH602-to-journal expansion.

Full requirements/checklist:
`tasks/active/mth602-final-multisurrogate-dqnguard-v1-research-program-v2.md`

Priority:
1. H1 backbone competence;
2. resolve H2 vs H4 (intrinsic target dependence vs useful target-blind selector);
3. H5 multi-surrogate DQNGuard if needed;
4. H3 STFT representation as a bounded lower-priority ablation.

Immediate sequence:
- audit all 10 canonical backbones for min-class F1 + epoch stability;
- HPO PA2-PA3, PA2-PA8, PA3-PA8 first using known-only evidence;
- initial stop when val macro-F1 >=0.95 and min-class F1 >=0.90;
- after each weak backbone freezes, immediately run both standard-DQNGuard directional OSR cells;
- use those target-open results only as an exploratory research-investment gate, never to choose per-cell HPO settings;
- if justified, freeze a tighter/stability-aware regime and apply a comparable budget across all 10 canonical pairs;
- recompute the full 20-cell matrix;
- rerun historical surrogate Rules A-C;
- pilot FFT vs STFT replacement vs FFT+STFT on the three PA1/PA4-confounded weak pairs plus a strong control, then expand only under a frozen rule;
- keep standard DQNGuard frozen through those controls;
- run H5 only after controls if surrogate dependence remains;
- final robustness target is 5 partition seeds x 10 model/training seeds after all method choices are frozen;
- before the earlier of the course due date and 2026-12-01, pivot to a complete report, slide deck, and durable post-finals journal checkpoint.

No new GPU job, merge, or trust widening is authorized by this planning interview.

## Fresh-chat checkpoint — H1 HPO wave0 live

This section supersedes the earlier GPU0-blocked snapshot. The authoritative source remains the JSON capsule.

### Exact bindings

- Workspace Control PR #640 head at checkpoint: `67e5d7a30ab9ce58c474376802f3ffd693a41281`
- PADataset HPO controller PR #37: **OPEN / DRAFT / UNMERGED**
- PR #37 exact live-wave head: `8b176ce931a1d802127ec2591d38ad0a4cedafb4`
- 24/24 immutable wave0 screen jobs admitted exactly once: 8 trial vectors × 3 weak canonical pairs
- lane split: 12 GPU0 / 12 GPU1
- **Do not advance PR #37 head while any exact-head-bound wave0 job is queued/running.**
- No merge authority is implied.

### GPU0 recovery

GPU0 originally produced four deterministic pre-epoch infrastructure OOM failures because unrelated host-local processes consumed nearly all VRAM. Those runs contain **no scientific HPO evidence**.

GPU0 subsequently recovered without authority widening or process killing:

- `PA2-PA3__t004__screen`
- run `44343691752`
- job `134940231711`
- **SUCCESS**
- artifact `14448887969`
- digest `sha256:10b264f29ad7e8440f7081aaf68741e74125cd52647bd890aed07d677a39e3d3`
- best epoch `7`
- best known-val macro-F1 `0.9636429463079487`
- known-test macro-F1 `0.9629794380523286`
- `target_test_consumed=false`

The epoch trace is highly unstable (e.g. macro-F1 ~0.167 on epochs 3/4/6, then ~0.964 on epoch 7), which reinforces the separate stability analysis. **Do not declare the pair competency-qualified from macro-F1 alone; the frozen gate also requires min-class validation F1 >= 0.90 and controller/extractor confirmation.**

Current GPU0 trial at checkpoint:
- `PA2-PA8__t004__screen`
- run `44343698092`
- job `134940254925`
- **IN_PROGRESS**

### GPU1 live

Current GPU1 trial at checkpoint:
- `PA2-PA8__t001__screen`
- run `44343612614`
- job `134939950045`
- **IN_PROGRESS**

Existing GPU1 queue should continue. Do not duplicate requests.

### Earlier GPU0 OOM trials

Four earlier wave0 instances failed before completing epoch 1 and are excluded from HPO ranking:

- `PA2-PA3__t000__screen`
- `PA2-PA8__t000__screen`
- `PA3-PA8__t000__screen`
- `PA2-PA3__t002__screen`

Now that GPU0 has recovered, **do not automatically resubmit them**. First let the admitted wave progress and ingest the available evidence; the deterministic controller should decide whether one infrastructure retry is actually required to complete the frozen screen set.

### Side branch already prepared

Branch:
`mth602-l2o-hpo-audit-v2`

Head:
`2e02e098245c2e3c877666174fcafd38dfb03056`

Validation:
`job-d0af3549-8c72-445d-a723-a4d53ee082b5` — **21 passed**

Contains:
- all-10 backbone competence/stability audit;
- strict known-validation-only artifact extraction;
- HPO ranking-input generation;
- finalist artifact -> temporary canonical matrix rebinding;
- automatic creation of the two standard-DQNGuard directional evaluation requests.

Keep this side branch separate until the live PR #37 wave is terminal because live requests are exact-head-bound to `8b176ce...`.

### Immediate next action

1. Re-read PR #640 JSON capsule and PR #37 live state.
2. Monitor only the already-admitted wave0 jobs.
3. Download/validate terminal artifacts as they arrive.
4. Feed terminal screen results through the strict known-only extractor/controller.
5. Rank by known-validation macro-F1 then min-class F1; target/test/OSR metrics must never affect HPO ranking.
6. Promote/freeze according to the documented gate-first policy.
7. After a weak pair freezes at macro >=0.95 and min-class >=0.90, run its two standard-DQNGuard directional OSR evaluations using the prebuilt downstream plumbing.
8. Apply the H1 exploratory gate only after those two directions are frozen: mean ΔUnknown-F1 >= +0.05, neither direction < -0.02, known-reject budget respected.
9. Continue autonomously until a genuine authority/operator gate or user-only scientific choice is reached.
