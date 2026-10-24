# EXTRACT Research Replay v0.1

Status: **RETROSPECTIVE SANITY CHECK — HINDSIGHT-CONTAMINATED**

Owner: `workspace-research-methodology-v1`

Methodology under test: `architecture/evidence-first-research-methodology.v0.1.md`

This document reconstructs selected Local EXTRACT scientific boundaries using the Evidence-First Research Methodology v0.1. It is not a claim that the methodology would certainly have made these choices prospectively. The analyst knows later EXTRACT history; each replay therefore declares an evidence cutoff and uses only evidence recorded at or before that cutoff, but human hindsight cannot be fully erased. Prospective shadow validation is required for actual validation.

## 1. Replay purpose

The replay asks whether a structured research state would have improved:

- residual localization;
- competing-hypothesis visibility;
- mechanism-family recognition;
- experiment discrimination;
- positive-invariant preservation;
- stopping/reopening discipline;
- distinction between technical invalidity and scientific falsification.

It does **not** score success by whether the methodology magically predicts the historically best later result.

## 2. Reconstructed mechanism families

The historical EXTRACT sequence contains several implementation families that are scientifically broader than their technology names.

### MF-1 — open-ended local generation under downstream guards

Premise:

> A local generative proposal/normalization path can directly produce sufficiently complete and grounded claims under bounded guard constraints.

Historical members include the initial Qwen EXTRACT architecture and subsequent bounded proposal/normalization waves.

### MF-2 — coverage-preserving retrieval/composition

Premise:

> The dominant residual can be addressed by selecting complementary evidence while preserving a strong teacher-blind retrieval baseline.

Historical members include balanced facility-location composition and protected residual augmentation.

### MF-3 — direct lexical proposition preservation

Premise:

> A bounded lexical proposition-level redundancy signal can safely identify replaceable evidence while preserving already-supported evidence.

Historical member:

- `DYNAMIC_SAME_PAGE_ALIGNMENT_SWAP_V1`.

### MF-4 — pairwise semantic redundancy certificate

Premise:

> A semantic representation/model can assign a pairwise score with a safe high-precision, nontrivial-recall operating point for certifying proposition redundancy.

Historical members:

- learned mutual-entailment / NLI certificate;
- dependency-derived predicate/argument certificate;
- AMR graph + Smatch certificate.

These implementations are technologically different. The replay treats the safe pairwise-certificate premise as shared evidence.

## 3. Positive invariant reconstructed from the history

### INV-1 — lexical preservation baseline

At the proposition-alignment checkpoint:

- candidate supports 8/13 teacher atoms;
- all 7/7 frozen source-aware controls are retained;
- residual e6.a is recovered;
- page ceiling is preserved.

This becomes an active invariant:

> Future semantic generalization SHOULD preserve the validated lexical proposition-alignment behavior unless it explicitly reopens that result with a replacement control.

Identity:

`research-engine@9566532288bf500db8997b9befcc339788609184:ALIGNMENT_AUGMENT_FEASIBLE`

## 4. Replay A — after Wave 7A.3 rejection

### Evidence cutoff

The valid Wave 7A.3 rejection plus source-aware/control evidence available before the post-Wave7A3 coverage design.

### Residual

Salience-aware intent generation did not preserve enough useful evidence under the fixed budget.

### Plausible hypotheses

- **H-A1 coverage composition:** relevant candidate evidence exists but selection across views fails to preserve complementary coverage.
- **H-A2 contribution/salience estimation:** the system lacks a reliable signal for scientific contribution.
- **H-A3 iterative residual search:** evidence needs cannot be satisfied in one static selection pass.

### Decision-value reading

A zero-generation coverage-composition diagnostic has lower cost and lower confound risk than training a new contribution model or adding iterative agent behavior.

### Replay recommendation

Test H-A1 first with a teacher-blind bounded composition diagnostic while preserving the source-aware baseline as a control.

### Historical comparison

The historical task selected `MULTIVIEW_SUBMODULAR_COVERAGE_DIAGNOSTIC_V1`, a zero-generation teacher-blind diagnostic.

### Replay interpretation

**CONSISTENT.** The historical choice is aligned with v0.1: it tested a premise cheaply before implementing a larger architecture.

## 5. Replay B — after COMPOSITION_NEGATIVE

### Evidence cutoff

Run `40032590597`, artifact `12535338326`, frozen verdict `COMPOSITION_NEGATIVE`.

Observed:

- verdict-eligible selector supports 4/13;
- retains 2/7 controls;
- frozen source-aware baseline reproduces 7/13 with 7/7 control retention;
- a non-verdict fixed quota reaches 8/13 and preserves 7/7, but is not eligible for post-hoc promotion.

### Residual

Naive balanced set coverage does not preserve semantic evidence even when page-level coverage looks strong.

### Plausible hypotheses

- **H-B1 utility mismatch:** teacher-blind retrieval/intent utility is not a sufficient proxy for semantic evidence preservation.
- **H-B2 residual evidence exists but requires an explicitly protected baseline rather than symmetric composition.
- **H-B3 the candidate signal needs a stronger semantic preservation certificate before swaps are allowed.

### Replay recommendation

Before adding a new model, test whether residual augmentation can be made monotonic with respect to the accepted baseline.

### Historical comparison

The task selected a lexicographic protected-baseline residual architecture, `ZERO_LOSS_RESIDUAL_AUGMENTATION_DIAGNOSTIC_V1`.

### Replay interpretation

**CONSISTENT.** It isolates whether preservation of the teacher-blind baseline is sufficient.

## 6. Replay C — after PROTECTED_AUGMENT_NEGATIVE

### Evidence cutoff

Run `40035904753`, artifact `12536818273`, verdict `PROTECTED_AUGMENT_NEGATIVE`.

Observed:

- all papers preserve the teacher-blind zero-loss utility;
- teacher support falls to 6/13;
- only 5/7 frozen control-supported atoms are retained;
- therefore source-aware intent-utility preservation does not imply semantic evidence preservation.

### Residual

The system needs a preservation signal closer to actual evidence redundancy than intent/retrieval utility.

### Plausible hypotheses

- **H-C1 direct proposition redundancy:** local proposition-to-proposition overlap may certify safe swaps more faithfully.
- **H-C2 learned semantic certificate:** surface overlap is insufficient; semantic equivalence is needed.
- **H-C3 no safe local swap signal exists; preserve the baseline and attack coverage elsewhere.

### Decision-value reading

A direct lexical proposition certificate is cheap, teacher-blind, and tests the immediate missing premise with low confound risk.

### Replay recommendation

Test direct proposition redundancy before learned semantic generalization.

### Historical comparison

The task selected `DYNAMIC_SAME_PAGE_ALIGNMENT_SWAP_V1`.

### Historical result

`ALIGNMENT_AUGMENT_FEASIBLE`: 8/13 support, 7/7 control retention, e6.a recovered.

### Replay interpretation

**CONSISTENT and informative.** This sequence is a strong example of progressively refining the hypothesis rather than blindly swapping architectures.

## 7. Replay D — after ALIGNMENT_AUGMENT_FEASIBLE

### Evidence cutoff

Run `40038661074`, artifact `12537639453`, result `ALIGNMENT_AUGMENT_FEASIBLE`.

### Residual

Lexical proposition alignment works as a preservation principle but remains incomplete; e1.a is still unrecovered and total support is 8/13 rather than strong.

### Plausible hypotheses

- **H-D1 semantic paraphrase residual:** lexical overlap misses meaning-preserving paraphrases.
- **H-D2 missing-evidence residual:** the remaining target is not available within the candidate set, so a stronger equivalence function cannot help.
- **H-D3 compositional residual:** support requires multiple evidence units rather than one substitute proposition.

### Methodology concern

The historical transition emphasized semantic-certificate generalization. v0.1 says the research state should preserve H-D2 and H-D3 as explicit competitors rather than silently assuming H-D1.

### Replay recommendation

A semantic-certificate test is eligible only if the design explicitly states that it tests H-D1 and does not imply that semantic similarity is the only residual explanation.

### Historical comparison

The task selected external-only `SCIENTIFIC_NLI_REDUNDANCY_CERTIFICATE_VALIDATION_V1`.

### Replay interpretation

**ELIGIBLE BUT NARROWER THAN THE FULL RESIDUAL.** The external-only teacher-blind test is methodologically clean, but the research state should retain non-semantic-certificate hypotheses.

## 8. Replay E — after NLI_CERTIFICATE_REJECTED

### Evidence cutoff

Run `40049443488`, artifact `12544077187`.

Observed:

- no SPARK threshold meets precision >= 0.95 and recall >= 0.05;
- selected threshold is null;
- SciNLI discrimination is nontrivial but does not satisfy redundancy safety;
- no EXTRACT teacher labels were used.

### Belief update

- learned mutual entailment is falsified **as the tested safe redundancy certificate**;
- the broader MF-4 pairwise semantic-certificate family is **WEAKENED**, not yet necessarily closed;
- H-D1 remains possible because failure of one certificate implementation does not prove semantic paraphrase is irrelevant.

### Candidate next mechanisms at the cutoff

- structured semantic units / tuples;
- dependency predicate/argument representation;
- AMR graph representation;
- claim/question decomposition;
- non-certificate residual mechanisms.

### Replay recommendation

A second MF-4 instantiation may still be justified, but the design MUST say what premise changes relative to learned entailment and freeze a family stopping rule before execution.

### Historical comparison

The task selected dependency-derived predicate/argument evidence units with SPARK safety plus FOBIE relation-fidelity validation.

### Replay interpretation

**DEFENSIBLE, but v0.1 would add a family-level stopping rule here.**

Example frozen family rule:

> If a materially different structured representation also cannot expose a safe SPARK operating point, do not test a third pairwise semantic-certificate representation without new premise-changing evidence.

This rule uses only evidence available after the NLI result.

## 9. Replay F — after PREDICATE_ARGUMENT_CERTIFICATE_REJECTED

### Evidence cutoff

Run `40057016505`, artifact `12546156155`.

Observed:

- no SPARK threshold meets precision >= 0.95 and recall >= 0.05;
- FOBIE held-out full relation recall = 4/153 = 2.61%;
- sentence unit coverage = 100%, so the relation-fidelity failure is not empty output;
- NLI had already failed the same safe SPARK operating-point requirement.

### Belief update

For MF-4:

- implementation 1: learned mutual entailment fails safe calibration;
- implementation 2: dependency predicate/argument representation fails safe calibration and scientific relation fidelity.

The shared family premise is now substantially weakened.

### Replay recommendation

Under the family stopping rule proposed at Replay E:

**CLOSE or at minimum strongly DEFER MF-4 pending premise-changing evidence.**

The next experiment should preferentially test a materially different role such as:

- evidence-obligation decomposition;
- missing/novel evidence detection;
- bounded evidence-set reasoning;
- targeted residual retrieval;

rather than a third representation feeding the same pairwise score → threshold → redundancy-certificate structure.

### Historical comparison

The historical task selected AMR graph redundancy versus claim/question decomposition and chose AMR for external validation.

### Replay interpretation

**METHODOLOGY/HISTORY DIVERGENCE.**

This is the strongest retrospective case for v0.1. The historical choice was carefully frozen and independently validated, but from the v0.1 mechanism-family perspective it reused the same core certification premise after two materially different failures.

This replay does **not** claim that AMR's later rejection was knowable in advance. It claims only that a structured methodology would have forced an explicit justification for reopening/retesting the family before spending implementation and GPU time.

## 10. Replay G — AMR execution failure versus AMR scientific result

### Evidence cutoff 1: pre-science failure

Run `40062934298`.

Observed:

- exact-SHA and GPU gates pass;
- amrlib installation fails before asset acquisition/parser/scoring;
- no scientific artifact exists.

### Required classification

`INVALID_EXPERIMENT / NOT_RUN`

No hypothesis or mechanism belief should change.

### Evidence cutoff 2: repaired scientific execution

Run `40125779107`, artifact `12573487854`.

Observed:

- end-to-end execution succeeds;
- Bio-AMR Smatch F1 = 0.3783772311 < 0.60;
- no SPARK safe calibration threshold exists;
- verdict = `AMR_GRAPH_CERTIFICATE_REJECTED`.

### Required classification

`FALSIFIED` for the tested AMR certificate.

MF-4 now has three negative implementations, two of which independently fail the same safe-calibration premise.

### Replay interpretation

**CLEAR FAMILY CLOSURE EVIDENCE.**

Do not retune the parser, threshold, beam count, tokenizer, or gates post hoc. Reopening MF-4 requires premise-changing evidence.

## 11. Initial reconstructed research graph

```text
Residual: incomplete local EXTRACT evidence support
  |
  +--> H: coverage/composition problem
  |      +--> balanced composition ----COMPOSITION_NEGATIVE----+
  |      +--> protected residual -----PROTECTED_AUGMENT_NEGATIVE
  |
  +--> H: preservation signal mismatch
  |      +--> direct lexical proposition alignment
  |             ----ALIGNMENT_AUGMENT_FEASIBLE----> INV-1
  |
  +--> H: lexical certificate misses semantic equivalence
         |
         +--> MF-4 pairwise semantic certificate
                +--> NLI ----------------NLI_CERTIFICATE_REJECTED
                +--> predicate/argument --PREDICATE_ARGUMENT_CERTIFICATE_REJECTED
                +--> AMR ----------------AMR_GRAPH_CERTIFICATE_REJECTED
```

The graph deliberately leaves other residual hypotheses open. A negative certificate family does not prove that retrieval, decomposition, composition, or evidence-set reasoning is solved.

## 12. What v0.1 appears to add

From this retrospective reconstruction, the methodology adds four things that were not consistently explicit in the historical workflow:

1. **Mechanism-family identity.** Different technologies can test the same premise.
2. **Family-level stopping/reopening rules.** Repeated premise failures create durable constraints on the next search.
3. **Competing residual hypotheses.** Selecting one architecture family does not silently erase other explanations.
4. **Decision-value experiment selection.** The next experiment is justified by what uncertainty it resolves, not only by plausibility.

## 13. What v0.1 does not yet prove

This replay cannot establish that the methodology improves live research because:

- the analyst knows later outcomes;
- the historical record may omit alternatives considered informally;
- replay quality depends on reconstruction fidelity;
- the framework could add bureaucracy without improving decisions.

The next genuine validation is prospective shadow mode at the next new EXTRACT architecture boundary.
