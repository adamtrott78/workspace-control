<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: `tasks/active/mth602-final-multisurrogate-dqnguard-v1.json`

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: `mth602-final-multisurrogate-dqnguard-v1`
- Status: active
- Current durable stage ID: `tracka_surrogate_selector_retest`
- Workspace Control PR: #640

## Immediate state

The frozen t007 competent-backbone bank is complete: **10/10 unordered leave-two-out backbones**.

The standard-DQNGuard directional OSR matrix is complete: **20/20 directional cells**.

Do not retrain or alter either frozen result set.

The matched-control matrix is **closed and validated at 20/20 canonical directional cells** from PADataset PR #56 exact head `17c991dd41c16099a679cc4ad81230c7616a0db1`.

Canonical recovery identities:
- PA4 <- PA3: run `45565602436`, job `139039493921`
- PA4 <- PA2: run `45565606606`, job `139039506686`

Excluded as superseded/noncanonical:
- original/recovery attempts `45509159615`, `45509140807`
- V1 replacements `45565324045`, `45565327001`
- prior duplicates `45517031611`, `45517036169`

Artifact audit:
- **20/20** unique directional result records COMPLETE
- **20/20** scientific receipts PASS
- **10/10** unique frozen backbones represented
- exact PR #56 candidate SHA preserved
- target labels used for tuning: **false**
- both controls fitted/frozen before target-test materialization: **true**
- standard DQNGuard threshold source: **known-only**
- no frozen recipe/checkpoint/threshold/selector/control/retry policy changed

Matched U-F1 summary:
- DQNGuard mean: **0.665583**
- DQN-IDS-style mean: **0.292854**
- VarMax mean: **0.706131**
- DQNGuard - DQN-IDS-style: **+0.372730 mean**, 14/20 wins, 95% paired-cell t-CI **[+0.156234, +0.589226]**
- DQNGuard - VarMax: **-0.040548 mean**, 12/20 wins, 95% paired-cell t-CI **[-0.136794, +0.055698]**

Target-level DQNGuard U-F1 deltas vs DQN-IDS / VarMax:
- PA1: **+0.440059 / -0.017370**
- PA2: **+0.272857 / -0.115109**
- PA3: **+0.687328 / +0.127035**
- PA4: **+0.017795 / -0.163635**
- PA8: **+0.445609 / -0.033660**

Geometry result: DQNGuard-minus-VarMax U-F1 increases with the frozen Rule-B confidence-geometry score (Spearman rho **+0.541**, p **0.0137**); no comparable monotonic signal was observed for frozen Rule-C centroid margin or feature-distance score.

## Multi-seed transition gate

The control prerequisite is satisfied, but **no seed admission is authorized yet because the seed identities are not actually frozen in durable state**.

The durable plan fixes the budget at:
- 5 partition seeds
- 10 model/training seeds per partition
- 10 canonical pairs
- 2 directional OSR cells per pair

But it does **not** contain:
- the explicit 5 partition-seed values;
- the explicit 10 model/training-seed values;
- a frozen DQN-seed policy (E1 still says `TBD; proposed fixed main-seed + separate sensitivity`).

Stage `final_seeded_robustness` explicitly requires those seed semantics before spending the 5x10 budget. Do not invent seed identities or admit jobs until that reviewed durable freeze exists.

## Controller/runtime state

PADataset workflow authority PR #57 is merged to main `7cfe0ab61cc16785f4d267273b48a63361c595dd`.

Lane A v4 trusted workflow:
- blob `39190413abbd801bd6d25c2166ac36a7a69968fb`
- controller policy SHA256 `ad776c6a684b430924e9000fca11ecf7d96e850122eac4aa2f439960c19891b7`

Lane B v9 trusted workflow:
- blob `6753795041090a5331a80354f59945be006ac889`
- controller policy SHA256 `42a5e2c09d2765e74458902d9701c0a4a50ecdb26424d5a54cef0da8a3284e8e`

The final anti-spam/liveness controller repair is active:
- source head `41ab0f9a47f993f1903947effceb6cda5bded6b1`
- controller SHA256 `9ee25a498e9e49a502590f60a701d5d1e3f0e392626204bec47ba628801eb102`
- transaction receipt `/var/lib/workspace-ci/v3/padataset-scientific/controller-repair/transactions/refresh-60a04761-869b-4be3-8a67-009a0c5f801a/receipt.json`

It fixes:
- GitHub rate-limit backoff using `X-RateLimit-Reset` / `Retry-After`
- skipping unrelated workflows before spending `/jobs` REST calls
- newest-active-run-first scanning
- bounded REST discovery after `MaxRunners` trusted demand is found

Operational proof: after the exhausted GitHub core quota reset, both GPU lanes automatically transitioned one existing control job from queued to running without controller restart or re-admission.

## Canonical Rule B/C replication

PADataset PR #55:
- branch `mth602-rulebc-selector-geometry-v1`
- exact head `59afa36826709531e64211af3c175e0378048f19`

Ignore superseded head `f7204ae2649de3a5525c8bd8eca6ab4b88753305` completely.

Canonical geometry runs:
- PA1-PA2: `45495502469`
- PA1-PA3: `45484994589`
- PA1-PA4: `45482247014`
- PA1-PA8: `45482253152`
- PA2-PA3: `45482259788`
- PA2-PA4: `45482263820`
- PA2-PA8: `45482269250`
- PA3-PA4: `45482273141`
- PA3-PA8: `45482281469`
- PA4-PA8: `45482289533`

All 10 scientific receipts PASS. Frozen historical formulas only. `target_labels_used_for_tuning=false`; `target_test_consumed=false`.

## Selector results already established

Historical:
- Rule A paper-era Spearman rho ~ -0.075
- Rule B paper-era Spearman rho ~ -0.552
- Rule C best simple feature rho ~ +0.406; exact best-surrogate selection 1/5

Repaired Rule A:
- target-centered Spearman rho +0.600, p 0.00516
- exact top-1 0/5
- top-2 4/5
- mean oracle regret 0.06420

Repaired Rule B:
- raw rho +0.263, p 0.262
- target-centered rho +0.335, p 0.148
- within-target permutation p ~0.196
- exact top-1 1/5
- top-2 3/5
- mean oracle regret 0.04876
- Rule A vs Rule B rho ~0.870
- partial Pearson after residualizing both on Rule A: r ~ -0.007, p ~0.978
- same-backbone delta Rule-B vs delta U-F1: rho -0.636, p 0.0479
- higher Rule-B direction wins only 2/10

Interpretation: Rule B is strongly redundant with Rule A and shows a Simpson-style reversal between cross-backbone and within-backbone behavior.

Repaired Rule C:
- raw rho +0.150, p 0.527
- target-centered rho -0.119, p 0.618
- within-target permutation p ~0.694
- exact top-1 2/5
- top-2 2/5
- mean oracle regret 0.01664

Rule C selections:
- PA1 -> PA4: exact winner
- PA2 -> PA3: 0.90754 vs oracle PA8 0.98476; regret 0.07722
- PA3 -> PA1: 0.98656 vs oracle PA2 0.98718; regret 0.00062
- PA4 -> PA1: exact winner
- PA8 -> PA4: 0.97389 vs oracle PA2 0.97926; regret 0.00538

Thus Rule C is exact 2/5, but 4/5 choices are within 0.01 U-F1 of oracle.

Same-backbone Rule C:
- higher centroid-margin direction wins 9/10
- only mismatch PA1-PA2
- exact sign-test p 0.02148
- delta centroid margin vs delta U-F1 rho +0.612, p 0.05997

Exploratory `feature_distance_score` is NOT the frozen Rule C scalar:
- within-backbone delta feature-distance vs delta U-F1 rho ~ -0.903, p ~0.000344
- mechanism evidence only; do not promote to a new selector

Target-aware confusion-exclusion diagnostic:
- target-centered rho ~ +0.530
- exact winner 4/5
- mean oracle regret ~0.000748
- oracle/mechanism diagnostic only; NOT deployable

## Scientific interpretation already established

Surrogate transferability is not intrinsic to a surrogate PA.

It depends jointly on:
1. leave-two-out backbone/representation geometry,
2. target-versus-surrogate directional role,
3. how the surrogate occupies the known confidence/feature manifold.

Rule C has meaningful same-backbone directional signal but poor cross-backbone calibration. Rule B is largely redundant with Rule A. The paper-era ordering was heavily entangled with weak backbone geometry; repaired within-target rankings are effectively uncorrelated with the old ordering.

## Matched controls closed

PADataset PR #56 exact head `17c991dd41c16099a679cc4ad81230c7616a0db1` is closed at **20/20 canonical directional cells**.

Canonical overnight recoveries:
- PA4 <- PA3: run `45565602436`, job `139039493921`
- PA4 <- PA2: run `45565606606`, job `139039506686`

Excluded from analysis as superseded/noncanonical:
`45509159615`, `45509140807`, `45565324045`, `45565327001`, `45517031611`, `45517036169`.

Validation:
- 20/20 unique directional result records COMPLETE
- 20/20 scientific receipts PASS
- 10/10 frozen canonical backbones represented
- target-test firewall preserved
- no frozen recipe/checkpoint/threshold/selector/control/retry policy changed

Matched U-F1:
- DQNGuard mean **0.665583**
- DQN-IDS-style mean **0.292854**
- VarMax mean **0.706131**
- DQNGuard - DQN-IDS-style: **+0.372730** mean, 14/20 wins, 95% paired-cell t-CI **[+0.156234, +0.589226]**
- DQNGuard - VarMax: **-0.040548** mean, 12/20 wins, 95% paired-cell t-CI **[-0.136794, +0.055698]**

Target-level DQNGuard deltas vs DQN-IDS / VarMax:
- PA1: +0.440059 / -0.017370
- PA2: +0.272857 / -0.115109
- PA3: +0.687328 / +0.127035
- PA4: +0.017795 / -0.163635
- PA8: +0.445609 / -0.033660

Frozen Rule-B confidence-geometry score correlates with DQNGuard-minus-VarMax U-F1:
Spearman rho **+0.541**, p **0.0137**. Frozen Rule-C centroid margin and feature-distance do not show a comparable monotonic matched-control delta signal.

## Final multi-seed robustness candidate

PADataset draft PR #58:
- branch `mth602-final-robustness-seed-freeze-v1`
- exact candidate head `3fd1454bc20b89580f14c2e319d9b33766ea14b5`
- base: PR #56 exact head `17c991dd41c16099a679cc4ad81230c7616a0db1`
- status: **VALIDATED CANDIDATE / NOT AUTHORIZED FOR SCIENCE**

Why PR #58 is needed: the frozen 5 x 10 design requires independent partition variance and model/training variance, but the legacy trainer's single `seed` controls both the data partition and training RNG/DataLoader order.

Candidate seed freeze:
- partition seeds: `[0,1,2,3,4]`
- training/model seeds: `[0,1,2,3,4,5,6,7,8,9]`
- standard-DQNGuard DQN seed for the main factorial: **42** (preserves the existing frozen evaluator)
- separate DQN-seed sensitivity: deferred; not a third factorial axis
- existing exact seed-0 matrix may count only as `partition_seed=0, training_seed=0` when exact recipe/artifact-compatible

Candidate RNG roles:
- `partition_seed`: split construction and deterministic OSR calibration-subset selection
- `training_seed`: Python/NumPy/PyTorch/CUDA model RNG plus DataLoader ordering/worker RNG
- fixed DQN seed 42: DQN initialization/fitting during the main factorial

Candidate validation:
- `job-515220a4-077f-404a-981b-aaecd662e677`: **4 passed**
- `job-abb4bb10-b745-411c-bc6d-0261fbb46bfe`: **12 passed**
- broader Stage03 deterministic source-string test is a proven pre-existing base failure, reproduced on PR #56 as `job-57d339a6-0773-43d6-992b-8fea6224526c`; it is not caused by PR #58

### Exact current gate

**SEED FREEZE ACCEPTED — SCIENCE ADMISSION AUTHORIZED THROUGH EXISTING BOUNDED PATHS.**

Accepted exact candidate SHA: `3fd1454bc20b89580f14c2e319d9b33766ea14b5`.

Accepted design:
- partition seeds `[0,1,2,3,4]`
- training/model seeds `[0,1,2,3,4,5,6,7,8,9]`
- fixed standard-DQNGuard DQN seed `42` for the main factorial
- separate DQN-seed sensitivity deferred

No merge authority was granted.

Next: generate and validate the immutable execution-package manifests, bind that derived exact SHA, then admit bounded train_backbone jobs on the two existing scientific GPU lanes.

Historical pre-acceptance gate text follows for provenance only:

Do **not** admit multi-seed science yet.

The numeric seed values were intentionally deferred in the earlier design and therefore were not previously authorized. PR #58 is a candidate proposal, not authority.

Required next action: explicitly accept the PR #58 seed freeze (partition seeds 0..4, training/model seeds 0..9, fixed DQN seed 42 for the factorial). After that acceptance:
1. bind the accepted exact candidate SHA;
2. generate immutable per-cell manifests;
3. validate the generated manifests;
4. admit through the existing bounded train_backbone / directional-evaluator paths only.

No merge authority is implied.

## Final robustness execution package

Seed freeze accepted and package validated.

PADataset PR #58:
- accepted candidate SHA `3fd1454bc20b89580f14c2e319d9b33766ea14b5`
- validated execution-package SHA `af4e2835b4e066a501b42e4b1558bee42cab9f8f`
- 500 immutable backbone manifests = 10 canonical pairs x 5 partition seeds x 10 training/model seeds
- partition seeds `[0,1,2,3,4]`
- training/model seeds `[0,1,2,3,4,5,6,7,8,9]`
- main-factorial standard-DQNGuard seed `42`
- seed-0 frozen artifacts are compatibility candidates only; do not rerun or count them until exact compatibility is checked
- validation receipt `job-5df04c94-5332-46fa-b5c0-e9ba244543d2`: **14 passed**

Authorized first wave:
- lane A: PA1-PA2, partition 0, training 1, `manifests/configs/mth602_final_robustness_v1/PA1-PA2/p00_t01.json`
- lane B: PA1-PA3, partition 0, training 1, `manifests/configs/mth602_final_robustness_v1/PA1-PA3/p00_t01.json`

Authority: bounded scientific admission is authorized through the existing `/lambda-scientific` and `/lambda-scientific-2` train_backbone paths. No merge authority and no frozen-policy changes.

First wave admitted:
- lane A — PA1-PA2 p00/t01: comment `7173344721`, run `45692779142`, job `139482306314`, QUEUED
- lane B — PA1-PA3 p00/t01: comment `7173345345`, run `45692782898`, job `139482318252`, QUEUED

Backfill rule: only after terminal SUCCESS on a lane, record artifact identity/digest and admit the next not-yet-admitted non-p00/t00 manifest on that same lane. Never duplicate an admitted/running/successful identity. Seed-0 p00/t00 cells remain compatibility candidates until exact artifact compatibility is proven.

## Final stage

Synthesize:
1. paper-era geometry,
2. repaired competent-backbone seed-0 geometry,
3. matched DQN-IDS/VarMax controls,
4. multi-seed robustness.

Then close the scientific task.

## Fresh-chat initialization

Use connected GitHub / Workspace tools directly.

Re-read Workspace Control PR #640 and:
`tasks/active/mth602-final-multisurrogate-dqnguard-v1.json`

before acting. Treat the capsule plus exact Git/runtime evidence as authoritative. Do not reconstruct stale state from previous chat prose when durable state disagrees.
