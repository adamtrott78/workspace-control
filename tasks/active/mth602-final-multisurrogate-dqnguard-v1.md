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
