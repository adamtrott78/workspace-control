# MTH602 / DQNGuard Expanded Research Program v2

Status: **AUTHORITATIVE REQUIREMENTS / IMPLEMENTATION PLAN**
Interview freeze: 2026-11-18
Task: `mth602-final-multisurrogate-dqnguard-v1`

This document supersedes the earlier assumption that the experimental program was ready for final synthesis. It converts the 2026-11-18 operator interview into a durable requirements checklist for the remainder of the MTH602 project and the post-finals journal expansion.

## 0. Program objective, framing, and non-negotiable rules

### 0.1 End state

- [x] Treat the MTH602 project as the first complete, rigorous slice of a larger journal-article program.
- [x] Work aggressively while time remains.
- [x] Before the earliest deliverable deadline, pivot to a durable complete project checkpoint with a coherent narrative, finished report, and finished slide presentation.
- [x] Preserve enough exact experiment/provenance state that the journal program can resume after finals without reconstructing decisions from chat history.
- [ ] Record the exact MTH602 due date when known.
- [ ] Research-to-deliverables pivot must occur early enough that both report and slides are complete before the earlier of the course due date and 2026-12-01.

### 0.2 Hypothesis priority

The program is ordered by the operator's scientific priorities:

1. **H1 — backbone-training quality explains an important portion of the historical Target–Surrogate behavior.**
2. **H2 / H4 — determine which is supported by evidence:**
   - H2: surrogate transfer remains genuinely target-dependent even with competent backbones.
   - H4: simple target-blind surrogate selectors become useful once backbone geometry is competent.
3. **H5 — multi-surrogate DQNGuard improves robustness if single-surrogate dependence remains after competent backbones/selectors.**
4. **H3 — FFT may hide temporal structure that STFT-derived features recover.** Important, but lower priority than H1/H2/H4/H5.

### 0.3 Narrative separation

**MTH602 framing**
- [x] H1 is allowed to be the narrative hook: forensic review found the historical matrix used one-epoch backbones, and retraining materially changed the matrix.
- [ ] The report/presentation must distinguish historical experimental weakness from the new controlled conclusions.
- [ ] The project should explain what was learned from the failure mode, not merely say that the old experiment was bad.

**Journal framing**
- [x] Do not make the journal contribution “the previous paper was poorly trained.”
- [ ] Frame the journal around robust open-world RF PA detection: backbone competence, surrogate-transfer structure, surrogate selection, representation, multi-surrogate methods, and uncertainty/variance.
- [ ] Historical MILCOM details are context/provenance, not the journal’s central contribution.

### 0.4 Scientific invariants

- [x] Standard DQNGuard remains frozen for all backbone-quality, selector-retest, and representation-control experiments.
- [x] Never use true target labels for backbone gradients, per-cell HPO selection, checkpoint selection, threshold selection, DQN fitting, surrogate selection, or retry decisions.
- [x] HPO uses known-only validation evidence.
- [x] Final target-open metrics are descriptive evaluation.
- [x] Any method change to DQNGuard is a separate H5 experiment after controls are established.
- [x] Exact SHA/config/checkpoint/artifact/partition/seed provenance is required.
- [x] Known-fit / known-guard / known-threshold / pseudo-open roles remain disjoint.
- [x] Known-reject budget remains the first operating constraint.

### 0.5 Primary endpoint hierarchy

For OSR comparisons:

1. known-reject budget satisfied;
2. Unknown F1;
3. OSR macro-F1;
4. AUROC.

Backbone known-validation macro-F1 and minimum-class F1 are **competency prerequisites**, not the final OSR objective.

---

# 1. CATEGORY A — Backbone competence and H1

## A0. Existing state

Current repaired matrix:
- 10 canonical unordered backbone pairs;
- 20 directional standard-DQNGuard evaluations;
- 17/20 cells improved vs the paper matrix;
- mean Unknown F1 increased from 0.4115 to 0.531841.

Written competency gate:
- known-validation macro-F1 >= 0.95;
- minimum known-class validation F1 >= 0.90.

At least three canonical backbones fail the macro gate:
- PA2–PA3: val macro-F1 ~0.9254; known-test macro-F1 ~0.9196;
- PA2–PA8: val macro-F1 ~0.9433; known-test macro-F1 ~0.9449;
- PA3–PA8: val macro-F1 ~0.8966; known-test macro-F1 ~0.8952.

All three weak pairs have PA1 and PA4 simultaneously in the known taxonomy, consistent with the recurring PA1↔PA4 confusion mechanism.

## A1. Weak-backbone HPO pilot — FIRST EXECUTION PRIORITY

### Requirements

- [ ] Audit all 10 canonical backbones for val macro-F1, min-class val F1, per-class confusion/F1, best epoch, and epoch-to-epoch stability.
- [ ] Begin HPO with exactly the three known macro-gate failures: PA2–PA3, PA2–PA8, PA3–PA8.
- [ ] Use only known-validation evidence.
- [ ] Initial pilot stopping condition: obtain a frozen candidate that clears both >=0.95 macro-F1 and >=0.90 min-class F1.
- [ ] Do not tune further from target-open outcomes within a pair.
- [ ] Preserve epoch-level validation traces so instability can later become a formal qualification metric if needed.

### Existing HPO implementation to reuse

Use the already-reviewed `padataset.l2o-repair-hpo-space.v1` search space:

- lr: log-float 5e-5 to 1e-3;
- weight decay: 0, 1e-5, 1e-4, 1e-3;
- center loss: 0, 0.05, 0.1, 0.2;
- label smoothing: 0, 0.05, 0.1, 0.15;
- entropy weight: 0, 0.01, 0.05, 0.1;
- dropout: 0.2, 0.3, 0.4, 0.5;
- grad clip: none, 0.5, 1, 2;
- scheduler: cosine or plateau;
- batch size: 8 or 16.

Existing resource ladder:
- screen: <=96 trials × 8 epochs, promote 24;
- refine: <=24 trials × 24 epochs, promote 6;
- finalist: <=6 trials × 60 epochs, promote 1.

### Pilot implementation plan

1. [ ] Implement/validate a gate-first HPO driver around the existing search space.
2. [ ] Run weak pairs concurrently across both A4500s when authority permits.
3. [ ] Search/rank only on known-validation macro-F1 then min-class F1.
4. [ ] Permit an early pilot stop once a recipe clears the written competency gate and has a valid frozen checkpoint.
5. [ ] Evaluate known-test only after recipe freeze.
6. [ ] Immediately run the two directional **standard DQNGuard** OSR cells corresponding to that canonical pair.
7. [ ] Compare against:
   - current repaired seed0 cell;
   - historical paper matrix as secondary context.
8. [ ] Record delta Unknown F1, OSR macro-F1, AUROC, known rejection, backbone metrics, and epoch stability.

### Important pilot interpretation rule

The immediate target-open OSR evaluations are an **exploratory investment gate**. They may answer “is deeper backbone work worth pursuing?” They must not select the next hyperparameters for the same target/surrogate pair.

### A1 decision gate

**Not yet frozen:** the phrase “improve significantly” needs a practical-effect threshold before launch.

Proposed default pilot gate:
- mean directional Unknown-F1 improvement for each repaired weak backbone >= +0.05 absolute versus the current repaired baseline; and
- neither direction regresses by more than 0.02 absolute; and
- known-reject budget remains satisfied.

This is a practical pilot gate, **not statistical significance**. Statistical claims wait for the multi-seed stage.

## A2. Uniform full-matrix training regime

### Branch 1 — weak pilot strongly supports H1

If all three weak backbones show substantial OSR benefit after competency repair:

- [ ] Add an explicit training-stability qualification criterion using only known-validation traces.
- [ ] Define a tighter competence/stability target.
- [ ] Give **all 10 canonical pairs the same search regime and tuning budget**, regardless of their current performance.
- [ ] Freeze each winning recipe from known-only evidence.
- [ ] Train/finalize all 10 canonical backbones under the same experimental regime.
- [ ] Run the full 20-cell standard-DQNGuard matrix.
- [ ] Compare old paper → first repaired matrix → uniformly tuned matrix.

### Branch 2 — weak pilot is mixed

- [ ] Do not tune toward target-open metrics.
- [ ] Analyze whether failure tracks epoch instability, PA1↔PA4 known confusion, min-class F1, calibration quality, or ceiling effects.
- [ ] Add a stability-aware known-only qualification criterion if justified.
- [ ] Freeze one uniform regime before retraining the complete 10-pair matrix.
- [ ] Continue H1 as an explanatory result only to the extent supported.

### Branch 3 — weak pilot shows little OSR benefit

- [ ] Stop treating additional backbone HPO as the dominant research direction.
- [ ] Retain the corrected matrix as evidence that one-epoch training was a confound, while emphasizing that closed-set competence alone does not solve surrogate transfer.
- [ ] Shift resources toward H2/H4/H5.
- [ ] Still complete any minimum qualification work needed for fair downstream comparisons.

## A3. H1 analysis package

Required outputs:
- [ ] backbone val/test macro-F1 by canonical pair;
- [ ] min-class F1 and confusion structure;
- [ ] epoch-stability metrics;
- [ ] directional Unknown F1;
- [ ] delta from historical and first-repair matrices;
- [ ] Pearson + Spearman relationships;
- [ ] pair-level and directional analyses;
- [ ] explicit separation between correlation and causal interpretation;
- [ ] project-facing figure showing how backbone competence altered the matrix.

---

# 2. CATEGORY B — Target-blind surrogate selection (H2 vs H4)

## B1. Exact historical Rules A–C retest

Do this **after a competency-qualified/uniform matrix exists**.

Freeze the formulas before reading the new target-open outcomes:

- **Rule A — guard-score calibration:** choose surrogate by calibration-open recall at the known-only threshold.
- **Rule B — confidence geometry:** use P1, P1-P2 gap, and entropy separation.
- **Rule C — feature geometry:** nearest-known-centroid distances and centroid-margin statistics.

Historical result:
- Rule A ~zero relationship and 2/5 top-1;
- Rule B negative relationship;
- Rule C strongest simple positive signal but 1/5 top-1.

### Requirements

- [ ] Reconstruct exact historical formulas and orientation from surviving code/evidence.
- [ ] Freeze them in a reviewed analysis contract.
- [ ] Run them on the new matrix without changing formulas from target results.
- [ ] Report Pearson r and Spearman rho.
- [ ] Report top-1 surrogate accuracy.
- [ ] Report rank of true best surrogate / mean reciprocal rank.
- [ ] Report oracle regret: best cell F1 minus selected-surrogate cell F1.
- [ ] Report selector stability across seeds in the final replication stage.

### Decision gate

- If one or more simple selectors become robustly useful: H4 gains support.
- If all remain weak after competent backbones: H2 gains stronger support and advanced selector work becomes justified.

## B2. Advanced selector stage — only if A–C remain insufficient

Candidate directions, in order:

1. [ ] pseudo-target validation using known classes as simulated unknowns;
2. [ ] route/confusion alignment;
3. [ ] learned selector from target-blind geometry/evidence;
4. [ ] combinations/ensembles of target-blind selector scores.

Requirements:
- [ ] no true-target labels in fitting/selection;
- [ ] leave-target-out or otherwise nested evaluation where possible;
- [ ] compare against A–C and simple fixed-surrogate baselines;
- [ ] retain oracle regret as the main deployment-facing selector metric.

---

# 3. CATEGORY C — STFT / representation ablation (H3)

H3 is lower priority than H1/H2/H4/H5; do not let representation work consume the whole project before the backbone pilot answers H1.

## C1. Current evidence

- [x] 360/360 canonical STFT overlay cache complete.
- [x] STFT-replacement backbone successfully trained.
- [x] PA1/PA4 trajectory diagnostic is nearly perfectly separable.
- [x] This establishes that ordering-sensitive information exists.
- [ ] It does **not** establish an end-to-end DQNGuard improvement over FFT.

## C2. Pilot representation experiment

Compare:

- **R0:** legacy FFT representation;
- **R1:** STFT replacement (current centroid/spread tracks replacing the FFT pair);
- **R2:** FFT + STFT augmentation, implemented as a separate architecture/input ablation.

### Pilot pairs

Primary relevant weak pairs:
- [ ] PA2–PA3 (known set contains PA1 + PA4);
- [ ] PA2–PA8 (known set contains PA1 + PA4);
- [ ] PA3–PA8 (known set contains PA1 + PA4).

Proposed strong control:
- [ ] PA1–PA2, whose known set does not contain both PA1 and PA4 and whose current backbone reaches the competency ceiling.

### Pilot implementation

1. [ ] Freeze matched partitions/seeds/training budget across R0/R1/R2.
2. [ ] Reuse standard DQNGuard unchanged.
3. [ ] Compare backbone competence first.
4. [ ] Freeze each backbone before target-open evaluation.
5. [ ] Run both directional OSR cells for every pilot pair/representation.
6. [ ] Measure Unknown F1, OSR macro-F1, AUROC, known rejection, per-class known confusion, and training stability.
7. [ ] Explicitly label PA1/PA4-motivated representation work as post-hoc/exploratory because the trajectory diagnostic already inspected those labels.

### Expansion gate

- [ ] Freeze a quantitative expansion rule before pilot target results are inspected.
- [ ] If STFT replacement or augmentation clears the rule, expand the winning representation to all 10 canonical pairs / 20 directional cells.
- [ ] If replacement helps PA1↔PA4 but harms controls, prioritize R2 augmentation over wholesale FFT replacement.
- [ ] If neither R1 nor R2 provides useful end-to-end benefit, stop H3 and preserve the mechanism diagnostic as a negative/interpretive result.

---

# 4. CATEGORY D — Standard DQNGuard control and H5 method development

## D1. Control requirement

- [x] All A/B/C experiments use **standard DQNGuard** first.
- [ ] Do not co-tune DQNGuard while testing backbone quality, selector quality, or representation.
- [ ] Preserve the 5% known-only threshold budget.

## D2. H5 trigger

H5 becomes a major focus if:
- competent backbones still show meaningful surrogate dependence; and/or
- Rules A–C and advanced target-blind selectors cannot reliably choose a low-regret surrogate.

## D3. Multi-surrogate continuation

Existing Architecture-B B0/B1/B2/B3 work is retained as evidence, but it is not allowed to replace the standard-DQNGuard controls.

Future implementation candidates:
- [ ] pooled multi-surrogate DQN;
- [ ] normalized ensemble of surrogate-specific DQNs;
- [ ] hybrid shared-DQN + deterministic multi-surrogate guard;
- [ ] full-matrix evaluation only after method selection is frozen on target-blind development evidence.

---

# 5. CATEGORY E — Final replication / variance program

Operator-selected rigor level: **full factorial 5 partition seeds × 10 training/model seeds** for the final frozen configuration.

## E1. Freeze before replication

Do not spend the replication budget until all of the following are frozen:
- [ ] backbone HPO/qualification policy;
- [ ] final representation choice;
- [ ] standard-DQNGuard control recipe;
- [ ] any selected surrogate rule or multi-surrogate method being claimed;
- [ ] seed semantics;
- [ ] result schema and aggregation.

## E2. Seed separation

Required:
- [ ] partition seed must be explicit and independent;
- [ ] model initialization/training seed must be explicit and independent;
- [ ] loader/sampler seed must be explicitly bound or documented;
- [ ] never overload one `seed` field to change partitions and initialization simultaneously.

Main final design:
- 5 partition seeds;
- 10 training/model seeds per partition;
- 10 canonical backbone pairs;
- 2 directional OSR cells per pair.

This implies up to **500 backbone trainings and 1,000 directional OSR evaluations per frozen representation/method configuration**. Therefore only final frozen configurations enter this stage.

## E3. DQN stochasticity — unresolved but non-blocking now

Proposed default:
- keep DQN seed fixed during the 5×10 backbone variance experiment so backbone/partition variance is identifiable;
- separately run a 10-DQN-seed sensitivity study on a representative subset or final selected configurations.

Do **not** silently multiply the main design by a DQN-seed axis without explicit freeze.

## E4. Required statistics

- [ ] mean, standard deviation, median, IQR;
- [ ] confidence intervals for main OSR metrics;
- [ ] per-target/per-surrogate variance;
- [ ] partition variance vs model-training variance;
- [ ] selector top-1/rank/regret stability;
- [ ] known-reject budget compliance frequency;
- [ ] failure/outlier accounting with provenance.

---

# 6. CATEGORY F — Compute and execution policy

- [x] Use both RTX A4500 GPUs aggressively when PADataset is the active workload.
- [x] Parallelize independent bounded experiments.
- [x] Avoid duplicate admissions.
- [x] Preserve one exact immutable request/config per job.
- [x] Use deterministic/candidate validation before expensive GPU work.
- [x] Do not run long experiments simply because GPUs are idle; jobs must belong to a frozen stage.
- [ ] Add queue/accounting views so total planned/running/completed/failed counts are visible.
- [ ] Estimate the 5×10 final replication cost from measured runtime before admission.

---

# 7. CATEGORY G — Deadline pivot and MTH602 deliverables

## G1. Deadline policy

Deliverables must be complete before the earlier of:
- the actual MTH602 project due date; or
- 2026-12-01.

Exact course due date is currently **TBD**.

Proposed operating rule:
- research continues aggressively until **5 days remain before the earliest deadline**;
- at that point, stop opening new experiment branches unless required to complete an already-selected core result;
- freeze a durable project evidence checkpoint and pivot to deliverables.

This buffer is a proposed default and can be tightened/relaxed once the exact due date is recorded.

## G2. Minimum complete project checkpoint before pivot

Must include:
- [ ] current best backbone-quality/H1 result;
- [ ] a complete standard-DQNGuard matrix appropriate to the chosen training regime;
- [ ] at least the exact Rules A–C retest if the qualified matrix exists;
- [ ] STFT pilot result if it completed cleanly; otherwise a clearly bounded mechanism/negative result;
- [ ] all result provenance and figures/tables needed for the report;
- [ ] no dangling claim that depends on an unfinished run.

## G3. Deliverables

### Written project report
- [ ] problem/motivation;
- [ ] forensic discovery and H1;
- [ ] corrected experimental methodology;
- [ ] backbone-quality experiment;
- [ ] surrogate-transfer matrix;
- [ ] selector analysis;
- [ ] representation/multi-surrogate results if completed;
- [ ] limitations;
- [ ] future journal program.

### Slide presentation
- [ ] hook: one-epoch / backbone-competence discovery;
- [ ] controlled repair;
- [ ] new matrix;
- [ ] why closed-set quality alone does/does not explain surrogate transfer;
- [ ] selector result;
- [ ] STFT or H5 result if mature;
- [ ] final takeaways and next work.

### Durable checkpoint
- [ ] exact repo heads;
- [ ] artifact IDs/digests;
- [ ] manifests/configs;
- [ ] complete result tables;
- [ ] experiment queue state;
- [ ] unresolved hypotheses;
- [ ] journal continuation plan.

---

# 8. CATEGORY H — Post-finals journal continuation

After MTH602 is submitted:

- [ ] resume from the durable checkpoint, not from chat prose;
- [ ] complete any matrix/representation/selector branches cut for deadline;
- [ ] complete full 5×10 replication;
- [ ] expand H5 if surrogate dependence remains;
- [ ] consider broader PA taxonomy / additional OTA conditions for external validity;
- [ ] build journal paper around the strongest supported H1/H2/H4/H5 findings.

---

# 9. CATEGORY I — MILCOM provenance/correction audit (deferred)

This is **not** part of the immediate experiment execution path.

After the MTH602 deliverables are safe:
- [ ] inspect the accepted MILCOM paper, final submitted manuscript, supplementary/repository artifacts, and presentation for any explicit statement of epochs/training duration for the Target–Surrogate Matrix;
- [ ] distinguish an omitted methodological detail from an explicit incorrect factual statement;
- [ ] document exact provenance conflict if one exists;
- [ ] discuss with advisor before contacting MILCOM;
- [ ] if an actual published factual error requires correction, determine the conference/IEEE correction mechanism from current policy.

No claim is made here that a correction is required.

---

# 10. Immediate implementation order

1. [ ] Freeze pilot practical-effect gate and exact weak-backbone HPO admission contract.
2. [ ] Audit 10-backbone min-class F1 + epoch stability.
3. [ ] Run HPO on PA2–PA3 / PA2–PA8 / PA3–PA8, maximally using both GPUs.
4. [ ] After each weak backbone freezes, run its two standard-DQNGuard directional OSR evaluations immediately.
5. [ ] Evaluate H1 pilot gate.
6. [ ] Freeze either tighter uniform matrix regime or mixed-result stability-aware regime.
7. [ ] Train the full 10-backbone matrix under that uniform regime.
8. [ ] Run full 20-cell standard-DQNGuard matrix.
9. [ ] Retest Rules A–C.
10. [ ] Run STFT representation pilot (can overlap with steps 6–9 only when protocol and GPU scheduling permit).
11. [ ] Expand STFT only if frozen pilot gate passes.
12. [ ] Run advanced selector and/or H5 only if triggered.
13. [ ] Freeze final configuration.
14. [ ] Execute 5 partition × 10 training-seed robustness program.
15. [ ] Pivot to MTH602 report/slides at the deadline gate regardless of remaining journal ambitions.
16. [ ] Resume remaining journal work after finals.

---

# 11. Unresolved decisions that do NOT block the first weak-backbone pilot

1. **Exact MTH602 due date.** Needed for the hard pivot calendar.
2. **Pilot “significant improvement” threshold.** Proposed default: mean two-direction ΔUnknown-F1 >= +0.05, no direction worse than -0.02.
3. **Epoch-stability metric/threshold.** Capture traces now; freeze criterion only if the weak pilot shows it is needed.
4. **STFT expansion threshold.** Must be frozen before STFT target-open pilot results are inspected.
5. **DQN seed axis in final replication.** Proposed: fixed in main 5×10; separate sensitivity study.
6. **Exact partition/model seed lists.** Freeze before final replication.
7. **Exact journal article scope.** Intentionally deferred until MTH602 results reveal which of H1/H2/H4/H5 are strongest.
