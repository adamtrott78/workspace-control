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

The matched-control matrix is now live from PADataset PR #56 at exact head `17c991dd41c16099a679cc4ad81230c7616a0db1`.

Current control status:
- **2 running**
- **18 queued**
- **0 complete**
- **0 failed**
- **0 duplicate admissions**

Running now:
- lane A: `PA1 <- PA2`, run `45509095061`, job `138851867447`
- lane B: `PA2 <- PA1`, run `45509096369`, job `138851868167`

Both are inside **Execute bounded scientific request** after exact-head verification, bounded-runner proof, checkout, and request validation all passed.

Do not re-admit any control request. The 20 immutable requests already exist exactly once, split 10/10 across the two GPU lanes.

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

## Matched controls now running

PADataset PR #56:
- branch `mth602-repaired-l2o-controls-v1`
- exact head `17c991dd41c16099a679cc4ad81230c7616a0db1`

Frozen controls:
- DQN-IDS-style: `dqn_ids_style_softmax3_external_surrogate_cap625_v1`
- VarMax: `varmax_surrogate_all_smoke_matched_l2o_v1`

DQN-IDS-style semantics:
- same exact frozen PyTorch backbone/checkpoint
- plain softmax3 DQN state
- hard DQN argmax action
- exactly 625 known + 625 external-surrogate validation samples
- no true-target calibration
- no DQNGuard bands or score threshold

VarMax semantics:
- historical `surrogate_all`
- historical `smoke` sweep
- known-validation pseudo-unknown calibration
- external surrogate is directional/backbone provenance only and is not consumed by VarMax

Target/test firewall:
- no target labels for tuning
- no target-open fitting
- no target test before final evaluation
- target test is not materialized until both controls are fitted/frozen
- control outcomes may not alter any frozen method

## What to do while controls run

Monitor only. Do not duplicate admissions.

When a cell closes:
1. verify workflow conclusion and scientific receipt;
2. collect exact artifact/result record;
3. preserve the frozen control semantics;
4. allow the controller to backfill the same GPU lane automatically.

If a cell fails, inspect the exact failure first. Do not blindly retry and do not change the control definition.

## After 20/20 controls close

Compute:
- DQNGuard minus DQN-IDS-style U-F1 and other frozen metrics per directional cell
- DQNGuard minus VarMax per directional cell
- aggregate means and uncertainty summaries
- target-level effects
- unordered-pair/backbone effects
- whether DQNGuard gains concentrate in particular target/surrogate/geometry regimes

Do not compare repaired DQNGuard to paper-era control numbers as if they were matched evidence.

## Then: final multi-seed robustness

Only after the matched control matrix closes.

Do not rely on seed-0 exact winner identity; PA3 and PA8 contain near ties.

Across the frozen seed set report:
- mean/std and confidence intervals
- surrogate winner frequency
- oracle-regret distributions
- Rule A/B/C picker stability
- confusion-exclusion diagnostic stability
- same-backbone directional-asymmetry stability
- DQNGuard-minus-control delta stability

No seed may use target/test/OSR evidence to change:
- backbone recipe
- checkpoint selection
- threshold policy
- control definition
- selector formula
- retry policy

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
