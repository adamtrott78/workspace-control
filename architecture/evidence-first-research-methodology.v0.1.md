# Evidence-First Research Methodology v0.1

Status: **EXPERIMENTAL / NON-CANONICAL**

Owner: `workspace-research-methodology-v1`

This document specifies an experimental outer-loop research methodology for AI/software artifact research. It is intentionally non-normative until retrospective replay and prospective shadow validation show that it improves research quality without unacceptable coordination cost.

## 1. Purpose

The workspace already has a strong inner engineering loop:

```text
freeze implementation scope
→ implement
→ CI / exact-SHA validation
→ execute
→ persist artifacts
→ reconcile durable state
```

That loop protects execution correctness, provenance, and reproducibility. It does not by itself answer a different question:

> Given incomplete evidence about why a research system is failing, what should we believe, what should we test next, and what result would change our decision?

This methodology owns that **outer scientific-reasoning loop**:

```text
observe residual
→ formulate competing hypotheses
→ organize evidence and assumptions
→ compare mechanism families
→ select the most decision-informative bounded experiment
→ freeze interpretation before outcome
→ execute through the existing engineering loop
→ classify the result
→ update beliefs / close or reopen mechanisms
→ select the next uncertainty
```

The methodology is intended for research programs where software artifacts, models, datasets, retrieval systems, agents, or other engineered systems are evaluated experimentally.

## 2. Methodological foundations

v0.1 combines four complementary traditions rather than treating any one as sufficient.

### 2.1 Strong inference

Platt's strong-inference formulation emphasizes explicit alternative hypotheses, experiments that discriminate among those alternatives, clean results, and repeated recycling of the hypothesis tree.

Operational consequence here:

- a research state SHOULD contain multiple plausible explanations for the current residual;
- an experiment SHOULD be preferred when different outcomes eliminate or materially weaken different hypotheses;
- "try another architecture" is not itself an experiment-selection rationale.

Reference: John R. Platt, "Strong Inference", *Science* 146(3642), 1964.

### 2.2 Design science research

Design Science Research Methodology (DSRM) treats artifact research as a cycle of problem identification, solution objectives, design/development, demonstration, evaluation, and communication.

Operational consequence here:

- the residual/problem and the objective for a solution MUST be stated separately from a proposed implementation;
- artifact construction is downstream of a research question and evaluation contract;
- evaluation must answer whether the artifact satisfies the objective, not merely whether it runs.

Reference: Peffers, Tuunanen, Rothenberger, Chatterjee, "A Design Science Research Methodology for Information Systems Research", *Journal of Management Information Systems* 24(3), 2007.

### 2.3 Preregistration / registered-report logic

Preregistration distinguishes prediction from postdiction by fixing hypotheses, measures, analysis, and interpretation commitments before seeing the relevant outcome.

Operational consequence here:

- every scientific experiment MUST freeze its interpretation table before outcome evidence is consumed;
- exploratory analysis after a result is allowed, but MUST be labeled exploratory and cannot retroactively change the frozen verdict;
- execution-envelope failures remain distinct from scientific outcomes.

References:
- Nosek et al., "The preregistration revolution", *PNAS* 115(11), 2018, DOI 10.1073/pnas.1708274114.
- Chambers et al., "Registered reports: realigning incentives in scientific publishing", *Cortex* 66, 2015, DOI 10.1016/j.cortex.2015.03.022.
- Munafò et al., "A manifesto for reproducible science", *Nature Human Behaviour* 1, 0021, 2017, DOI 10.1038/s41562-016-0021.

### 2.4 Decision-theoretic / optimal experimental design

Bayesian and decision-theoretic experimental design frames experiment selection around utility: the best experiment is not necessarily the most elaborate one, but the one whose possible observations most improve the decision.

Operational consequence here:

- where quantitative priors and likelihoods are justified, expected information gain or expected utility MAY be computed;
- where they are not justified, the methodology MUST NOT invent pseudo-probabilities;
- the default selection rule is therefore an ordinal **Decision Value** comparison over discrimination, decision relevance, cost, and confound risk.

Reference: Chaloner & Verdinelli, "Bayesian Experimental Design: A Review", *Statistical Science* 10(3), 1995, DOI 10.1214/ss/1177009939.

## 3. Two-loop model

### Outer loop: scientific reasoning

Owns:

- research objective;
- observed residual;
- competing hypotheses;
- assumptions;
- mechanism-family comparison;
- experiment-selection rationale;
- frozen scientific gates;
- interpretation table;
- scientific result;
- belief update;
- stopping/reopening decisions.

### Inner loop: engineering execution

Owns:

- exact code/workflow identity;
- dependency/runtime state;
- implementation;
- CI;
- execution routing;
- exact artifacts/hashes;
- technical failure classification;
- reproducibility and durable reconciliation.

A failure in the inner loop MUST NOT be treated as evidence against a scientific hypothesis unless the scientific treatment of that failure was itself predeclared.

Example:

```text
package install fails before model execution
→ INVALID_EXPERIMENT / NOT_RUN

frozen benchmark executes successfully and misses its gates
→ valid scientific evidence
```

## 4. Research-state model

A research state is a time-indexed snapshot of what may legitimately influence the next scientific decision.

### 4.1 ResearchQuestion

The decision-relevant question being investigated.

Required properties:

- scope;
- decision that the answer will affect;
- terminal or intermediate objective;
- evidence cutoff.

### 4.2 Residual

An observed gap between the current system and the research objective.

A residual is not a proposed solution.

Examples:

- evidence is available but not selected;
- target support remains incomplete;
- accepted controls regress;
- a verifier abstains on a bounded class;
- latency or cost exceeds an objective.

A residual MUST cite the evidence that establishes it.

### 4.3 Hypothesis

A falsifiable explanation for one or more residuals.

Each hypothesis SHOULD include:

- statement;
- predicted observations;
- evidence currently supporting it;
- evidence currently weakening it;
- explicit falsifiers;
- current state: `OPEN`, `SUPPORTED`, `WEAKENED`, `FALSIFIED`, or `DEFERRED`.

Hypotheses are explanations, not model names.

### 4.4 Assumption

A premise used by a hypothesis, mechanism, experiment, or decision but not directly established by current evidence.

Assumptions are first-class because hidden assumptions often survive multiple failed implementations.

### 4.5 MechanismFamily

The underlying causal/computational premise shared by candidate implementations.

Examples:

- pairwise semantic score → threshold → redundancy certificate;
- retrieve → decompose obligation → targeted residual retrieval;
- evidence-set coverage optimization;
- constrained generation followed by independent verification.

A mechanism family is intentionally broader than an architecture or model.

States:

- `OPEN`;
- `DEFERRED`;
- `CLOSED`;
- `REOPENED`.

### 4.6 CandidateArchitecture

A concrete implementation proposal belonging to one or more mechanism families.

Architecture comparison MUST state what scientific premise differs, not merely what package/model differs.

### 4.7 EvidenceItem

A provenance-bearing observation available before the research-state cutoff.

Evidence kinds may include:

- benchmark result;
- artifact;
- external paper;
- diagnostic measurement;
- accepted control;
- negative result;
- execution failure;
- independent review finding.

Evidence MUST record its source identity and observation time.

### 4.8 Invariant

A previously accepted behavior that future work should preserve unless explicitly reopened.

An invariant is not eternal truth. It is a default preservation obligation.

Reopening an invariant requires:

- explicit rationale;
- new evidence;
- a replacement experiment that measures the cost of abandoning it.

### 4.9 ExperimentDesign

A frozen scientific contract.

Required elements:

- question;
- target uncertainty;
- competing hypotheses;
- discrimination claim;
- controls;
- metrics;
- gates;
- possible outcome classes;
- interpretation for each outcome;
- invalidation conditions;
- stopping rule;
- execution budget;
- teacher/data leakage constraints;
- what a PASS authorizes;
- what a FAIL closes or weakens.

### 4.10 ScientificResult

A valid experiment outcome classified as one of:

- `SUPPORTED`: evidence materially supports the tested hypothesis/mechanism;
- `WEAKENED`: evidence moves against it but does not meet the frozen falsification condition;
- `FALSIFIED`: frozen evidence satisfies a predeclared rejection condition;
- `INCONCLUSIVE`: experiment executed validly but does not discriminate enough to support a decision;
- `INVALID_EXPERIMENT`: the scientific question was not validly tested.

Project-specific verdicts MAY coexist with this generic classification.

### 4.11 BeliefUpdate

The explicit transition from one research state to the next.

It records:

- which hypotheses changed state;
- which assumptions changed status;
- which mechanisms closed/deferred/reopened;
- which invariants remain active;
- which uncertainty is now highest priority.

### 4.12 StoppingRule and ReopeningCondition

A stopping rule states when a line of inquiry is no longer worth another implementation under the current evidence.

A reopening condition states what new evidence would justify revisiting it.

A mechanism family MUST NOT be reopened merely because a different model, prompt, package, or threshold is available.

## 5. Evidence-First Research Loop

### Phase 0 — establish the evidence cutoff

Create a research-state snapshot.

Freeze:

- repository/result identities;
- allowed evidence;
- timestamp/cutoff;
- unresolved decision.

This makes retrospective replay and prospective reasoning auditable.

### Phase 1 — state the residual

Write the smallest evidence-backed statement of what remains wrong or unknown.

Bad:

> We need better semantic extraction.

Better:

> Current mechanism preserves the accepted controls but leaves five target atoms unsupported; existing evidence does not yet establish whether the residual is retrieval, recognition, composition, decomposition, or selection.

### Phase 2 — enumerate competing hypotheses

Generate multiple explanations before generating architectures.

Requirements:

- at least two plausible hypotheses when the evidence permits;
- each hypothesis predicts something observable;
- overlapping hypotheses are allowed but their overlap must be explicit.

If only one hypothesis is plausible, record why alternatives were excluded.

### Phase 3 — map evidence, assumptions, and mechanism families

For every hypothesis:

- list supporting evidence;
- list contradicting evidence;
- expose assumptions;
- identify mechanisms that would test or exploit it;
- identify prior mechanism-family failures that constrain the search.

At this phase, literature research asks:

> What mechanisms have evidence that changes the plausibility of our hypotheses?

It does not ask merely:

> What architecture is popular?

### Phase 4 — generate candidate experiments before choosing architectures

Prefer experiments that test premises before large implementations.

Candidate experiment classes include:

- oracle/ceiling diagnostic;
- ablation;
- counterfactual test;
- external validity test;
- bounded representation test;
- controlled head-to-head;
- small prototype;
- full architecture benchmark only when cheaper tests cannot discriminate.

### Phase 5 — select by Decision Value

An experiment is **eligible** only if:

1. it targets a priority uncertainty;
2. at least two plausible outcomes would produce meaningfully different next decisions, unless it is a direct falsification test;
3. its result can be interpreted without moving the gates afterward;
4. it has an execution/invalidity boundary;
5. it is no larger than necessary to test its premise.

Among eligible experiments, compare these dimensions ordinally:

- **discrimination breadth** — how many plausible hypotheses/mechanisms can the outcomes separate?
- **decision relevance** — will the result change what we do?
- **falsifiability** — can the favored premise actually lose?
- **independence** — can the premise be tested without contaminating teacher labels or target benchmark decisions?
- **cost** — compute, implementation time, external dependencies, human review;
- **confound risk** — how many interacting changes could make the result ambiguous?
- **reuse value** — does the experiment produce useful evidence even on failure?

Do not collapse these into a fabricated numerical score unless a project has justified weights or a probabilistic utility model.

The selected experiment MUST document why lower-cost discriminating alternatives are insufficient.

### Phase 6 — freeze the interpretation table

Before implementation/execution, freeze:

| Outcome class | Evidence pattern | Interpretation | Authorized next action |
|---|---|---|---|
| support | predeclared positive gate | premise survives | bounded next design step |
| partial/weak | mixed gate | premise remains uncertain | targeted diagnostic only |
| reject/falsify | predeclared negative gate | premise closes/weakens | update research state |
| invalid | scientific execution not completed | no scientific update | repair execution only |

Project-specific rows replace these generic examples.

A PASS MUST say exactly what it authorizes. It must not silently authorize production, integration, or a larger scientific claim.

### Phase 7 — execute through the engineering loop

Once frozen, the scientific design does not change during ordinary implementation.

Technical fixes MAY occur when they preserve:

- scientific inputs;
- metrics;
- gates;
- interpretation;
- controls;
- model/data identity where identity is part of the test.

A technical fix that changes the scientific question requires a new frozen design.

### Phase 8 — classify and update

After execution:

1. establish whether the experiment was valid;
2. apply the frozen interpretation table;
3. persist the raw observations separately from interpretation;
4. create a belief update;
5. close/defer/reopen mechanisms according to the frozen rules;
6. select the next **uncertainty**, not the next technology.

## 6. Mechanism-family discipline

A recurring failure mode in AI research is to treat implementation diversity as hypothesis diversity.

For example:

```text
NLI model → pairwise score → threshold → redundancy decision
AMR graph → pairwise score → threshold → redundancy decision
```

These may use very different technology while sharing a scientific premise:

> a universal pairwise representation/similarity score has a safe operating point that can certify redundancy.

The research state SHOULD therefore contain both:

- implementation-specific evidence;
- mechanism-family evidence.

### Closure

A mechanism family is eligible for `CLOSED` when the current evidence satisfies a predeclared family stopping rule, for example:

- a direct independent experiment falsifies the family premise;
- multiple materially distinct instantiations fail for the same premise-relevant reason;
- a ceiling/oracle diagnostic shows the mechanism cannot reach the objective.

No universal fixed failure count is imposed in v0.1.

### Reopening

A closed family may be reopened only by **premise-changing evidence**, such as:

- a new independent dataset that invalidates the original failure assumption;
- a new mechanism that removes the causal failure mode rather than merely replacing a component;
- evidence that the prior experiment was invalid;
- a changed research objective that makes the old gate irrelevant.

Availability of a newer model alone is not premise-changing evidence.

## 7. Positive-invariant discipline

Negative evidence prevents repeated dead ends. Positive evidence prevents regression.

Every research state SHOULD name the strongest accepted invariants.

A new experiment must either:

- preserve them;
- measure them as controls; or
- explicitly reopen them with justification.

This guards against "improvement" that solves one residual by destroying already-validated behavior.

## 8. Retrospective replay

Retrospective replay is useful for testing whether the methodology organizes historical decisions coherently, but it is vulnerable to analyst hindsight.

Therefore replay MUST:

- declare an exact evidence cutoff;
- exclude all later artifacts/results from the replay input;
- state the hypotheses that were defensible from the cutoff evidence;
- record the methodology's recommended uncertainty/experiment;
- compare it with the historical decision only after the replay decision is frozen;
- disclose that the analyst may still possess human hindsight.

Retrospective replay is a **sanity check**, not proof of predictive validity.

True validation requires prospective shadow use.

## 9. Prospective shadow validation

Before becoming mandatory, the methodology runs beside a live research task.

At a scientific boundary:

1. the methodology snapshots the evidence state;
2. it records residuals, hypotheses, mechanism-family state, and recommended experiment class;
3. it commits that shadow recommendation before the future result;
4. the owning scientist proceeds independently;
5. later, compare:
   - whether the methodology surfaced missed hypotheses;
   - whether it predicted a more discriminating/cheaper experiment;
   - whether it avoided a repeated premise;
   - whether it preserved accepted invariants;
   - whether its overhead was useful.

The shadow lane MUST NOT block the owning research task.

## 10. Promotion criteria

v0.1 is not canonical merely because it is plausible.

Promotion requires evidence from both retrospective and prospective evaluation.

Candidate promotion dimensions:

- **residual clarity**: did the framework improve localization of what remained unknown?
- **hypothesis breadth**: did it expose credible alternatives that would otherwise be omitted?
- **experiment discrimination**: did proposed tests separate hypotheses rather than merely benchmark an implementation?
- **falsifiability**: did favored ideas have real ways to lose?
- **premise reuse control**: did it prevent accidental retesting of closed mechanism families?
- **invariant preservation**: did it prevent regression of accepted positive evidence?
- **failure informativeness**: did negative outcomes reduce uncertainty?
- **research efficiency**: did it avoid unnecessary implementation or compute?
- **coordination overhead**: did the framework create excessive process cost?

Final v1 disposition:

- `PROMOTE_TO_CANONICAL_RESEARCH_WORKFLOW`;
- `REVISE_METHODOLOGY`;
- `REJECT_METHODOLOGY_V1`.

## 11. Ontology compatibility

v0.1 deliberately models research state with explicit typed entities and provenance so it can later map into a knowledge graph.

Potential future relations include:

```text
Residual --explained_by--> Hypothesis
EvidenceItem --supports--> Hypothesis
EvidenceItem --weakens--> Hypothesis
ExperimentDesign --tests--> Hypothesis
ExperimentDesign --tests_premise_of--> MechanismFamily
ScientificResult --falsifies--> Hypothesis
ScientificResult --closes--> MechanismFamily
Invariant --constrains--> ExperimentDesign
BeliefUpdate --supersedes--> ResearchStateSnapshot
ReopeningCondition --reopens--> MechanismFamily
Decision --justified_by--> EvidenceItem
```

This task does **not** require RDF, ontology-native payloads, or `SemanticObservationV1`.

The ontology should consume a validated methodology model later, rather than forcing ontology shape into the methodology prematurely.

## 12. Immediate EXTRACT shadow interpretation

The current EXTRACT history is useful because it contains:

- invalid experiments distinct from scientific failures;
- positive and negative frozen results;
- repeated technology changes that sometimes share an underlying mechanism;
- accepted positive invariants;
- teacher-blind external validation;
- explicit gates and exact provenance.

At the current cutoff, the methodology should not choose EXTRACT's next architecture. Its role is to record constraints on the next decision:

- accepted lexical proposition-alignment preservation remains positive evidence;
- NLI, dependency predicate/argument, and AMR certificate results are negative evidence;
- the next architecture search should begin from competing explanations of the surviving residual;
- another implementation of the same pairwise-certificate premise requires explicit premise-changing evidence.

The EXTRACT owner remains scientifically independent.

## 13. References

1. Platt JR. Strong Inference. *Science*. 1964;146(3642):347-353.
2. Peffers K, Tuunanen T, Rothenberger MA, Chatterjee S. A Design Science Research Methodology for Information Systems Research. *Journal of Management Information Systems*. 2007;24(3):45-77.
3. Nosek BA, Ebersole CR, DeHaven AC, Mellor DT. The preregistration revolution. *PNAS*. 2018;115(11):2600-2606. DOI: 10.1073/pnas.1708274114.
4. Chambers CD, Dienes Z, McIntosh RD, Rotshtein P, Willmes K. Registered reports: realigning incentives in scientific publishing. *Cortex*. 2015;66:A1-A2. DOI: 10.1016/j.cortex.2015.03.022.
5. Munafò MR, Nosek BA, Bishop DVM, et al. A manifesto for reproducible science. *Nature Human Behaviour*. 2017;1:0021. DOI: 10.1038/s41562-016-0021.
6. Chaloner K, Verdinelli I. Bayesian Experimental Design: A Review. *Statistical Science*. 1995;10(3):273-304. DOI: 10.1214/ss/1177009939.
