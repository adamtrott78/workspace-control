# Research Methodology Prospective Validation v0.1

Status: **EXPERIMENTAL**

Owner: `workspace-research-methodology-v1`

This document defines how the Evidence-First Research Methodology is evaluated prospectively without overstating independence or confusing process conformance with predictive validity.

## 1. Why a separate validation protocol is necessary

A methodology can appear successful for the wrong reason.

If the methodology lane gives the owning scientist constraints before the scientist selects an architecture, then later agreement between the methodology and that architecture is **not independent evidence** that the methodology would have selected the same design on its own.

Likewise, a good scientific result does not prove the methodology was good; a falsified hypothesis can come from an excellent experiment.

Prospective validation therefore evaluates distinct claims separately.

## 2. Evidence classes

### 2.1 Process-quality evidence

Question:

> Did the research design exhibit the behaviors the methodology is intended to produce?

Examples:

- explicit residual;
- multiple plausible hypotheses;
- mechanism-family comparison;
- smallest discriminating experiment;
- frozen interpretation;
- invalid-experiment boundary;
- preserved positive invariants;
- stopping/reopening rules.

This may be evaluated after a design is frozen. It does not prove architecture-selection independence.

### 2.2 Pre-result interpretation evidence

Question:

> Before the scientific result existed, did the methodology freeze an interpretation that remained coherent when the result arrived?

Requirements:

- exact design/result identity;
- shadow snapshot committed before result;
- outcome classes and interpretations fixed before result;
- no mutation of the shadow after result;
- later comparison reports PASS / REVISE / NOT_EVALUABLE.

This is the strongest evidence currently available in the shared Git workflow.

### 2.3 Architecture-selection evidence

Question:

> Would the methodology independently prioritize the same uncertainty/experiment family as the owning scientist?

This requires independence from the owner's design process.

If methodology guidance was supplied before design selection, mark architecture-selection evidence `NOT_EVALUABLE`.

Do not infer independence from timestamp ordering alone when shared guidance could have shaped the owner.

### 2.4 Outcome-quality evidence

Question:

> Did the selected experiment reduce uncertainty regardless of whether the favored hypothesis passed?

Useful negative results count positively when they:

- falsify a real premise;
- separate competing explanations;
- close or defer a mechanism family;
- preserve a reusable invariant;
- constrain the next decision.

A positive benchmark result that leaves the causal question unresolved is weaker methodology evidence than an informative falsification.

## 3. Evaluation rubric

Use ordinal dispositions instead of a fabricated aggregate score.

For each prospective boundary evaluate:

- `residual_clarity`
- `hypothesis_breadth`
- `mechanism_family_distinction`
- `experiment_discrimination`
- `falsifiability`
- `positive_invariant_preservation`
- `invalid_experiment_boundary`
- `post_hoc_resistance`
- `next_action_calibration`
- `research_efficiency`
- `coordination_overhead`
- `architecture_selection_independence`

Allowed dispositions:

- `PASS`
- `PROMISING_NOT_PROVEN`
- `REVISE`
- `FAIL`
- `NOT_MEASURED`
- `NOT_EVALUABLE`

Every disposition must cite evidence.

## 4. Diagnostic-depth rule

A valid result does not automatically authorize an immediate architecture jump.

After each scientific result:

1. reconstruct the residual and competing hypotheses;
2. identify what uncertainty actually remains;
3. ask whether a cheaper diagnostic can distinguish the remaining explanations;
4. prefer that diagnostic when it can materially change the next decision;
5. only then select a larger architecture family.

This rule prevents a predeclared interpretation table from becoming overly prescriptive.

An outcome's `authorized_next_action` should therefore be read as an **admissible scientific region**, not a mandatory next implementation.

Example:

```text
PARTIAL result
→ budget collision contributes but is incomplete
→ before choosing decomposition vs iterative retrieval,
   test whether missing evidence is absent, shallow/distributed,
   deep, or merely unrecognized
→ then select the next mechanism
```

## 5. First prospective case: evidence frontier

Frozen shadow:

`architecture/extract-prospective-shadow-frontier.v0.1.json`

Actual result:

- `ADDITIVE_FRONTIER_PARTIAL`
- e6.a recovered at budget 26;
- all seven immutable controls retained;
- e1.a absent through budget 32.

Evaluation:

- outcome class: PASS;
- interpretation: PASS;
- invariant preservation: PASS;
- falsifiability: PASS;
- post-hoc resistance: PASS;
- architecture-selection independence: NOT_EVALUABLE;
- next-action calibration: REVISE.

The revision is important: the frozen shadow suggested moving directly to comparison of decomposition versus iterative retrieval, while the owning EXTRACT task instead inserted a smaller automatic-intent exposure diagnostic. That diagnostic produced `SHALLOW_DISTRIBUTED_EXPOSURE`, materially reducing uncertainty before the next planner design.

This is evidence for the diagnostic-depth rule.

## 6. Shared-state contamination rule

Until a sealed/blind commitment mechanism exists, the methodology lane SHOULD NOT publish a prescriptive next-architecture recommendation into shared durable state before the EXTRACT owner freezes its own design if architecture-selection independence is intended to be evaluated.

Instead, the methodology lane may:

- evaluate already-frozen design quality;
- freeze pre-result outcome interpretation;
- record mechanism-family constraints already established by prior evidence;
- measure result informativeness;
- record methodology revisions after results.

This avoids making the evaluator part of the treatment.

## 7. Promotion evidence

Methodology promotion requires a body of evidence spanning:

- prospective interpretation quality;
- repeated process-quality usefulness;
- at least one architecture-selection case where independence is genuinely defensible;
- evidence that methodology overhead is acceptable;
- evidence that the framework avoids repeated premises or unnecessary implementation effort;
- no unresolved systematic failure in next-action calibration.

A single successful case is insufficient.

## 8. Current implication

Evidence-First Research Methodology v0.1 remains experimental.

The first prospective interpretation case is positive but reveals one real revision candidate:

> add explicit diagnostic-depth semantics so outcome tables constrain the next scientific region without forcing premature architecture selection.
