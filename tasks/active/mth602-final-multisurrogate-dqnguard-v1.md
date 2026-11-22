<!-- CURRENT-FRESH-CHAT-CHECKPOINT-2026-11-22 -->
## CURRENT FRESH-CHAT CHECKPOINT — 2026-11-22

**Authoritative source:** re-read Workspace Control PR #640 current head, then `tasks/active/mth602-final-multisurrogate-dqnguard-v1.json`. Treat JSON as authoritative over older sections below.

### Current scientific stage

`t007_fullmatrix_expansion_admitted_osr_diagnostics_pending`

The t007 program has moved from a 3-pair pilot into uniform full-matrix execution.

### Existing t007 evidence

- PA2–PA3: COMPLETE, known-validation macro-F1 `0.9935446126501883`, min-class F1 `0.99026518966096`.
- PA2–PA8: COMPLETE, known-validation macro-F1 `0.9876063834565111`, min-class F1 `0.9811405985319028`.
- PA3–PA8: identical clean rerun still active under workflow run `44954748830`, rerun job `137275754026`.

PA2–PA8/t007 already has terminal standard-DQNGuard OSR on both directions:

- PA2<-PA8 Unknown-F1 `0.984758990646242`, delta vs repaired Track-A `+0.18372599064624195`.
- PA8<-PA2 Unknown-F1 `0.9792627621225628`, delta `+0.2222517621225628`.
- frozen H1 investment gate: **PASS**.

These OSR values are diagnostic only and cannot select the t007 recipe, checkpoint, retry, or pair freeze.

### PADataset PR #41 — exact locked execution head

Draft PR: `#41`  
Branch: `mth602-t007-fullmatrix-osr-v1`  
Exact head: `85bc8cb667a000d3fc544b33f8e96a6775074561`  
Validation: `job-ff6313ff-d592-4d64-b883-30760a3beb2e` — **22 passed**

Do not advance this head while exact-head-bound jobs are queued/running.

### New PA2–PA3/t007 OSR diagnostics

Exactly two standard-DQNGuard requests were admitted:

- PA2<-PA3 — comment `7082531548`
- PA3<-PA2 — comment `7082531870`

Both use the clean PA2–PA3/t007 artifact `14736363148`, digest `sha256:3419dd982709fccdfccce0a044260542a904ce9c86e1c4ef4e8e8bcb76c96b4d`.

### Seven remaining t007 backbone admissions

All seven missing canonical pairs were pre-admitted with the exact frozen t007 optimizer/training recipe and 60-epoch budget:

- GPU lane A: PA1–PA2, PA1–PA4, PA2–PA4, PA4–PA8.
- GPU lane B: PA1–PA3, PA1–PA8, PA3–PA4.

This is intentional speculative parallelism based only on the known-validation t007 lead. OSR results cannot retroactively select, cancel, modify, or prioritize these jobs.

### Unified t007 wave observer

Use the 10-pair host-local dashboard when the operator wants to view the full t007 expansion as one wave:

- renderer: `scripts/mth602_t007_fullmatrix_local_dashboard.py`
- launcher: `scripts/mth602_t007_fullmatrix_tmux.sh`
- session: `mth602-t007-wave`
- validation: `job-3a07dfe4-d086-4a6c-acd5-3663dc24c3c2` — **2 passed**
- refresh loop: **0 gh calls, 0 GitHub/provider API calls**
- view: all 10 canonical pairs, pair-weighted overall completion, per-run ETA, approximate two-lane wave ETA, GPU telemetry
- `Ctrl+C`: detach client, keep dashboard alive
- reattach: `tmux attach -t mth602-t007-wave`

### PA1–PA2/t007 newly terminal — OSR provenance gate

Host-local observer at 2026-11-22 13:27 EST shows PA1–PA2/t007 **SUCCESS** (best epoch 2, displayed val macro-F1 1.0000, total 48:38).

Standard-DQNGuard OSR is prepared conceptually for both directions:

- PA1<-PA2
- PA2<-PA1

Do **not** admit them until the exact provider binding is known: workflow run ID, workflow job ID, artifact ID, and artifact digest. The connected GitHub surface can fetch jobs/artifacts by run ID but does not expose issue_comment run listing. PA1–PA2 finished before the local observer persisted run IDs.

Observer repair `e8b3b084ca13563dba32f8953ec343bc54b54101` now captures `GITHUB_RUN_ID` locally for active/future t007 trainings with zero provider polling; validation `job-68404c7e-1eac-45aa-b958-a92f76270dea` passed 2/2.

### Immediate next action

Monitor only PR #41 exact head and the existing PA3–PA8/t007 rerun. Do not duplicate any OSR or training admission.

When PA2–PA3/t007 OSR becomes terminal, ingest it descriptively against the frozen H1 gate. As each new t007 backbone completes, strict-extract known-validation macro-F1 and min-class F1. Once all ten canonical t007 backbones are provenance-valid, construct the complete standard-DQNGuard directional OSR matrix.


---

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

This section supersedes earlier wave0 snapshots. The authoritative source remains the JSON capsule.

### Exact bindings

- Workspace Control PR #640 pre-checkpoint head: `eede3734422caf2b901cbf1cd5221a4a366e168a`
- PADataset PR #37: **OPEN / DRAFT / UNMERGED**
- exact live-wave head: `8b176ce931a1d802127ec2591d38ad0a4cedafb4`
- 24/24 immutable screen jobs admitted exactly once; duplicates: 0
- current snapshot: **4 SUCCESS / 6 infrastructure FAILURE / 2 IN_PROGRESS / 12 QUEUED**
- **Do not advance PR #37 head while any exact-head-bound wave0 job is queued/running.**
- No merge authority is implied.

### Strict known-validation ingestion

Validated downstream extractor/ranker:
- branch `mth602-l2o-hpo-audit-v2`
- head `2e02e098245c2e3c877666174fcafd38dfb03056`
- extractor blob `2522663949d62eddfb106017de0d8f8e91528004`
- ranker blob `371ec41e496c48ed10c4ceac9904f4d1b31c809d`
- validation receipt `job-d0af3549-8c72-445d-a723-a4d53ee082b5` — **21 passed**

Ranking rule from the reviewed code/tests:
`min-class feasible (>=0.90) first -> val macro-F1 -> val min-class F1`.

Target/test/OSR fields are forbidden from ranking input.

Successful screens ingested so far:

| Trial | Run | Artifact | Best epoch | Known-val macro-F1 | Min-class val F1 | Screen gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| PA2-PA3 t001 | 44343604175 | 14448511271 | 3 | 0.9155588 | 0.8602978 | fail |
| PA2-PA8 t001 | 44343612614 | 14452562651 | 5 | 0.9532694 | 0.9255079 | pass |
| PA2-PA3 t004 | 44343691752 | 14448887969 | 7 | 0.9636429 | 0.9453491 | pass |
| PA2-PA8 t004 | 44343698092 | 14453324498 | 7 | 0.9023084 | 0.8369748 | fail |

Current provisional successful-only ordering:
- PA2-PA3: `t004 > t001`; current winner clears both screen thresholds.
- PA2-PA8: `t001 > t004`; current winner clears both screen thresholds.
- PA3-PA8: no successful screen artifact ingested yet.

These are **not promotions and not freezes**. The bounded screen wave is still incomplete, and only a terminal finalist may freeze a pair.

### Infrastructure-only failures

Six GPU0 trials are excluded from scientific ranking because CUDA OOM occurred before usable scientific evidence:

- PA2-PA3 t000 — run 44343583046
- PA2-PA8 t000 — run 44343586571
- PA3-PA8 t000 — run 44343593644
- PA2-PA3 t002 — run 44343625925
- PA2-PA8 t002 — run 44343634712 / job 134940029562 / tiny failure artifact 14444819572
- PA3-PA8 t002 — run 44343640671 / job 134940050111 / tiny failure artifact 14446805993

The two newly confirmed t002 failures have the same external-VRAM OOM signature as the earlier failures. **Do not retry them while the admitted queue is still progressing.** After wave ingestion, the deterministic controller may decide whether any missing trial needs one infrastructure retry; that decision must remain target/test/OSR-blind.

### Active jobs

- GPU1: `PA3-PA8__t001__screen` — run `44343618795` / job `134939973259` — **IN_PROGRESS**
- GPU0: `PA2-PA3__t006__screen` — run `44343738180` / job `134940393559` — **IN_PROGRESS**

Both are inside the bounded scientific execution step.

### Queued jobs

12 already-admitted requests remain queued:

- PA2-PA3 t003 — 44343647186
- PA2-PA8 t003 — 44343655822
- PA3-PA8 t003 — 44343668555
- PA3-PA8 t004 — 44343707552
- PA2-PA3 t005 — 44343716800
- PA2-PA8 t005 — 44343721573
- PA3-PA8 t005 — 44343731277
- PA2-PA8 t006 — 44343747081
- PA3-PA8 t006 — 44343756497
- PA2-PA3 t007 — 44343766238
- PA2-PA8 t007 — 44343773182
- PA3-PA8 t007 — 44343778619

Do not duplicate any request.

### Epoch stability observations

Instability remains substantial and is preserved as a second-stage scientific variable, not a new gate. Examples:
- PA2-PA3 t004: validation macro-F1 ~0.167 on epochs 3/4/6, then 0.9636 on epoch 7.
- PA2-PA8 t001: peak 0.9533 at epoch 5, then 0.6404 by epoch 8.
- PA2-PA3 t001: peak 0.9156 at epoch 3, then 0.3001 by epoch 8.

Do not invent a stability threshold until the weak-pair pilot supplies enough evidence.

### Immediate next action

1. Re-read PR #37 current workflow state.
2. Monitor only the 24 already-admitted wave0 runs.
3. Download and provenance-check each new SUCCESS artifact.
4. Strict-extract known-validation macro-F1 and min-class F1; keep target/test/OSR fields out of ranking input.
5. Keep infrastructure failures excluded from ranking.
6. Do not issue a retry while already-admitted wave0 work remains queued/running.
7. When the bounded screen wave is sufficiently terminal, run the deterministic ranker and let it decide top-2 refine promotion and whether any one-time infrastructure retry is necessary for missing evidence.
8. Do not advance PR #37 until its exact-head-bound queue is dead.
9. Only a terminal 60-epoch finalist that clears macro >=0.95 and min-class >=0.90 may freeze a pair.
10. After freeze, use the prebuilt downstream plumbing for the two standard-DQNGuard directional evaluations and then apply the frozen H1 +0.05 / -0.02 gate.


## Fresh-chat checkpoint — H1 HPO wave0 attempt2 infrastructure retries

This section supersedes the earlier wave0-live checkpoint. The authoritative source remains the JSON capsule.

### Attempt1 closure

- PADataset PR #37 remains **OPEN / DRAFT / UNMERGED** at exact head `8b176ce931a1d802127ec2591d38ad0a4cedafb4`.
- Original wave0: **24/24 terminal**.
- Scientific successes: **18**.
- Infrastructure-only CUDA OOM failures: **6**.
- The six OOMs are exactly `t000` and `t002` for PA2-PA3, PA2-PA8, and PA3-PA8; they failed before a usable validation epoch and remain excluded from scientific ranking.
- No target/test/OSR evidence is used for HPO selection.

### Provisional observed leaders

Strict checkpoint extraction confirms the strongest observed attempt1 candidates:

| Pair | Trial | Known-val macro-F1 | Min-class val F1 |
| --- | --- | ---: | ---: |
| PA2-PA3 | t003 | 0.9879791290 | 0.9818181818 |
| PA2-PA3 | t005 | 0.9783293686 | 0.9670056497 |
| PA2-PA8 | t003 | 0.9884992938 | 0.9827105410 |
| PA2-PA8 | t007 | 0.9820379425 | 0.9725561352 |
| PA3-PA8 | t005 | 0.9837465208 | 0.9752290465 |
| PA3-PA8 | t001 | 0.9749894729 | 0.9619534355 |

All six artifacts preserve `target_test_consumed=false`.

These leaders are **provisional only**. They are not promotion authority because two deterministic screen candidates per pair were missing from attempt1.

### Why one retry is required

Wave0 was frozen as eight deterministic candidates per unresolved pair. Because `t000` and `t002` lack scientific evidence, promoting from only six candidates would silently change the reviewed screen set. The missing candidates could in principle outrank the observed leaders.

The durable controller therefore requires exactly one infrastructure retry of each missing deterministic trial before refine promotion.

### Attempt2 admissions

Exactly one rerun was requested for each failed workflow job on 2026-11-19. No new issue-comment admission, trial ID, hyperparameter vector, or candidate head was created.

| Trial | Workflow run | Original job | Attempt2 state at request |
| --- | ---: | ---: | --- |
| PA2-PA3 t000 | 44343583046 | 134939846163 | QUEUED |
| PA2-PA8 t000 | 44343586571 | 134939857208 | QUEUED |
| PA3-PA8 t000 | 44343593644 | 134939880831 | QUEUED |
| PA2-PA3 t002 | 44343625925 | 134939997323 | QUEUED |
| PA2-PA8 t002 | 44343634712 | 134940029562 | QUEUED |
| PA3-PA8 t002 | 44343640671 | 134940050111 | QUEUED |

Each workflow is now `run_attempt=2`.

### Immediate next action

1. Monitor only these six attempt2 retries.
2. Do **not** issue any additional retry.
3. Do **not** advance PR #37 while they remain queued/running.
4. Strict-extract any successful attempt2 artifacts with `experiments/l2o_hpo_extract.py`.
5. Once all six are terminal, rank the complete screen evidence with `experiments/l2o_hpo_rank.py`.
6. Promote the top **2 per pair** to the frozen 24-epoch refine stage.
7. Promote the best refined candidate per pair to a 60-epoch finalist.
8. Freeze only a terminal finalist clearing validation macro-F1 >=0.95 and min-class F1 >=0.90.
9. Only after freeze, run the two standard-DQNGuard directional OSR cells and apply the H1 investment gate.


## Fresh-chat checkpoint — H1 60-epoch finalists launched (2026-11-21)

This section supersedes earlier HPO execution snapshots. The authoritative source remains the JSON capsule.

### Exact bindings

- Workspace Control PR #640 handoff branch: `mth602-final-multisurrogate-dqnguard-resume-20261116-v1`
- PADataset PR #37: **OPEN / DRAFT / UNMERGED**
- exact finalist head: `ab87931408651b0b3516d910b13474822fb2a93d`
- finalist validation receipt: `job-17bc8ee0-68f1-4b7d-9853-7b0c30285bee` — **16 passed**
- selection evidence remains **known-validation only**
- target/test/OSR evidence used for HPO/finalist selection: **false**
- no merge authority is implied

### Three frozen pair winners

| Pair | Winner | Scheduler | Refine known-val macro-F1 | Min-class val F1 |
| --- | --- | --- | ---: | ---: |
| PA2-PA3 | t005 | cosine, frozen T_max=60 | 0.9661089632 | 0.9473315427 |
| PA2-PA8 | t007 | plateau | 0.9876063835 | 0.9811405985 |
| PA3-PA8 | t001 | plateau | 0.9749894729 | 0.9619534355 |

### Live finalist runs

- **GPU0 / IN_PROGRESS** — PA2-PA8 t007 — run `44924427484` / job `136907282120`
- **GPU1 / IN_PROGRESS** — PA3-PA8 t001 — run `44924431170` / job `136907293141`
- **GPU0 / QUEUED** — PA2-PA3 t005 deterministic replay — run `44924828921` / job `136908531021`
  - admission comment `7065682477`
  - explicit user authority granted 2026-11-21
  - frozen cosine `scheduler_t_max_epochs=60`
  - replay starts from epoch 0; **do not claim exact 24->60 resume**
  - prefix reference: repair run `44635259724`, artifact `14593806373`
  - first 24 epochs must reproduce the frozen repaired trajectory closely enough for deterministic replay acceptance before finalist evidence is accepted

### Why PA2-PA3 t005 is a replay

The epoch-24 repair state saved model/center-loss/optimizer/scheduler/global RNG/history, but it omitted the dedicated training DataLoader shuffle generator and persistent-worker RNG state. Exact epoch-25 continuation therefore cannot be proven. The user explicitly authorized the scientifically clean fallback: deterministic epoch-0 replay under the identical frozen T_max=60 protocol, with first-24-epoch prefix verification.

### Dashboard

Canonical local observer:
`scripts/mth602_finalists_local_dashboard.py`

Expected tmux session:
`mth602-finalists`

The dashboard is read-only, refreshes every second, uses root-local runner/process/result telemetry, and makes **zero GitHub API calls** in the refresh loop.

### Immediate next action

1. Read the JSON capsule first.
2. Re-read the three exact workflow runs; do not trust this snapshot if GitHub has advanced.
3. Do not duplicate any finalist admission.
4. Do not advance PADataset PR #37 head while any finalist is queued/running.
5. Strict-extract terminal finalist evidence using known-validation only.
6. For PA2-PA3 t005, verify the replay's first 24 epochs against run `44635259724` before accepting its finalist evidence.
7. Pair freeze requires validation macro-F1 >=0.95 and minimum known-class validation F1 >=0.90.
8. Only after a pair freezes may its two standard-DQNGuard directional OSR evaluations run.
9. Target-open results are exploratory H1 investment evidence only; they must never retroactively choose HPO settings.


## H1 finalist OSR overlap — 2026-11-21

Two finalist pairs are now frozen from **known-validation-only** evidence while PA2-PA3 t005 continues its deterministic epoch-0 replay:

- **PA2-PA8 t007**: artifact `14719755202`; best epoch `18`; val macro-F1 `0.9876063834565111`; minimum known-class F1 `0.9811405985319028` (PA1); competence gate **PASS**; `target_test_consumed=false`.
- **PA3-PA8 t001**: artifact `14717512029`; best epoch `5`; val macro-F1 `0.9749894729486733`; minimum known-class F1 `0.9619534355479841` (PA4); competence gate **PASS**; `target_test_consumed=false`.

PADataset PR #37 remains frozen at exact head `ab87931408651b0b3516d910b13474822fb2a93d`; it has **not** advanced.

A separate draft overlap candidate was created for pair-specific post-freeze directional OSR:

- PADataset PR #38
- branch: `mth602-h1-finalist-osr-overlap-v1`
- exact head: `51ba24cf9a9a53234225fbbf6fa41e4073bdac8d`
- diff: exactly the canonical matrix plus the four PA2/PA8 and PA3/PA8 directional request manifests
- candidate-pytest receipt: `job-ce7c50ab-2c7a-4eb7-8070-d3e662e69efe`
- validation: **20 passed**
- accepted evaluator implementation files are exact blob matches to successful evaluator head `b141020bf7b171571879abdf18a836132e80d1d5`.

Four GPU1 request comments were submitted exactly once on PR #38:

- `7067493529`: PA2 <- PA8
- `7067493896`: PA8 <- PA2
- `7067494169`: PA3 <- PA8
- `7067494602`: PA8 <- PA3

Workflow-run IDs are not yet durably observed; do not infer admission until GitHub returns them.

The scientific firewall remains strict: these target-open results may only apply the predeclared H1 exploratory investment gate. They must **never** influence PA2-PA3 replay acceptance, checkpoint choice, HPO settings, or retry decisions.

Frozen baseline Unknown-F1 values for the investment comparison are PA2<-PA8 `0.801033`, PA8<-PA2 `0.757011`, PA3<-PA8 `0.054209`, and PA8<-PA3 `0.424513`. The gate remains mean two-direction ΔUnknown-F1 >= `+0.05`, neither direction regresses by more than `-0.02`, and the known-reject budget remains satisfied.


### H1 OSR overlap compatibility repair + corrected admissions

The first two PR #38 GPU1 attempts reached the evaluator but failed deterministically **before DQN fitting and before any OSR result metrics** because the finalist-derived target-quarantine config had `open_val_frac=0` and PR #38 had omitted the already-proven Track-A surrogate-calibration adapter.

PR #38 was repaired by restoring the exact accepted `experiments/l2o_directional_contract.py` blob `6c3218cc068e4e994209408560888064d1796f19` from successful evaluator head `b141020bf7b171571879abdf18a836132e80d1d5`. The adapter keeps the true target quarantined while deriving surrogate calibration with `open_val_frac=0.15`, balanced/required surrogate `val_open` semantics. New exact PR #38 head: `d7ba2c754d7d281651f4119ba79544ec6f6e89f6`.

Focused candidate validation receipt `job-145dc8ac-fc63-4566-8b1d-17c6a9704ab6`: **26 passed**.

Corrected GPU1 runs:
- PA2 <- PA8: `44939698874 / 136953961053`
- PA8 <- PA2: `44939701110 / 136953968815`
- PA3 <- PA8: `44939702954 / 136953974301`
- PA8 <- PA3: `44939705618 / 136953982458`

Obsolete pre-repair runs `44937283229` and `44937285567` are deterministic pre-DQN compatibility failures and must not count as scientific evidence. Old-head queued runs `44937287676` and `44937290780` are stale-head non-evidence. PR #37 remains frozen at `ab87931408651b0b3516d910b13474822fb2a93d`.

## Fresh-chat handoff — lane-B v8 activation blocked by installed-state digest drift

Authoritative JSON remains `tasks/active/mth602-final-multisurrogate-dqnguard-v1.json`.

Current durable handoff head: `71fba4a3d72479c68ec68503f1a1ff0f26362b02`.

### Confirmed live state

- PADataset PR #53 was merged; PADataset `main` is `51073327c688d243961a0caabbb5358cc065ced1`.
- Both scientific GPU workflows on PADataset `main` now use `timeout-minutes: 360`.
- Lane-B new workflow blob: `8375dd0a0733b01de38f677dee58a373d3adcb48`.
- Lane-B predecessor v7 blob: `85dc8f289a972dddbb1a838d5596def6d872118b`.
- Workspace Control PR #648 is the v7→v8 trusted-workflow refresh lineage.
- Exact validated activation/launcher head attempted: `b3914a7d9caf6ba4e6d8086d50a01e2c63d0b0b8`.
- Zero-work smoke run `45074031090` is terminal cancelled.
- Lane-B currently has zero queued/in-progress workflow runs.

### Activation attempt and exact blocker

Operator launcher reached:

```
LANEB_PROVIDER_ZERO_WORK=PASS
PAD_MAIN=51073327c688d243961a0caabbb5358cc065ced1
LANEB_WORKFLOW_BLOB=8375dd0a0733b01de38f677dee58a373d3adcb48
```

Then failed inside `candidate.verify_installed(BASE_MANIFEST)` with:

```
lambda_ci_v3_reconciler.ReconcileError:
PADataset scientific managed addition digest drift:
/etc/workspace-ci/v3/controllers/padataset-scientific-single-gpu-v1.json
```

Manifest: `/etc/workspace-ci/v3/install-manifest.json`.

The failure occurs before `consume_authority()`, before lane-B controller stop, before v8 receipt write, and before controller-policy mutation. Therefore the v8 activation did **not** mutate live lane-B state.

### Required next action

Diagnose the managed-addition digest drift through the existing authorized install/reconciler lineage. Compare the current root-owned file and the digest recorded in `install-manifest.json`; determine whether the drift came from a later authorized repair or is unintended. Preserve current state and fail closed.

Do **not** hand-edit the controller file, bypass `verify_installed()`, widen root/Workspace Shell authority, re-admit the three training jobs, or rerun PA3-PA8 yet.

After the drift is reconciled: revalidate the v8 candidate, activate v8, verify lane-B trusts blob `8375dd0a0733b01de38f677dee58a373d3adcb48`, run a zero-work smoke, then re-admit exactly PA1-PA3, PA1-PA8, and PA3-PA4 once.

