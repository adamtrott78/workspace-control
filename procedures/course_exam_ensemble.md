# Course exam-ensemble preparation procedure

## Purpose

Build a reusable evidence-weighted model of an upcoming course exam, simulate many plausible exam blueprints, and use the resulting ensemble to choose representative practice while keeping student mastery separate from exam prediction.

This procedure is appropriate when enough evidence exists to infer:
- exam structure or question count;
- covered scope and explicit exclusions;
- instructor problem families or recurring assessment style;
- current homework/class-example archetypes;
- optionally, historical exams from the same instructor/course.

It is especially useful when the exact questions are unknown but the **distribution of plausible questions** can be constrained.

## Core idea

Use the pipeline:

`source evidence -> scope/model -> predictive priors -> blueprint ensemble -> recurring structure -> representative practice -> mastery feedback -> new instructor evidence -> posterior update`

The method has two different goals that must never be conflated:

1. **Prediction** — approximate what the instructor is likely to test.
2. **Training** — spend study time where the student most needs work.

Prediction and training may use the same topic taxonomy, but they require separate weights.

## Non-negotiable distinction: predictive versus mastery weights

### Predictive weights
Estimate exam composition from evidence such as:
- explicit current instructor exam guidance;
- review-session statements;
- current lectures/transcripts;
- current homework and in-class exercises;
- syllabus/scope boundaries;
- current distributed handouts;
- historical exams/assignments, at lower authority.

Predictive weights must **not** increase merely because the student is weak at a topic.

### Mastery weights
Estimate what the student needs to practice from:
- fresh independent attempts;
- delayed transfer;
- errors;
- hesitation/slow method selection;
- guided versus independent work;
- stale or missing evidence.

Mastery weights intentionally distort practice toward weaknesses and therefore must not be used to estimate likely exam composition.

## Evidence authority

Before assigning predictive weights, define an authority order. A default order is:

1. current explicit exam statements and exclusions;
2. current review session;
3. current lecture/instructor emphasis;
4. current homework/class examples/handouts;
5. current syllabus and required supplemental material;
6. recent historical exams from the same instructor/course;
7. older historical material or student artifacts.

Project/course-specific authority may override this ordering, but it must be explicit.

Historical evidence may support continuity; it must never override current exclusions or direct instructor guidance.

## Phase 1 — recover scope and exam invariants

Record:
- exam date/duration;
- question count and point structure when known;
- permitted aids;
- covered sections/lectures/homework;
- explicit exclusions;
- named question families;
- instructor response-length expectations;
- known grading/scaffolding style.

Separate **hard invariants** from **uncertain weights**.

Examples of hard invariants:
- Q1 is True/False;
- one double-sided sheet allowed;
- Section X excluded;
- full Procedure Y will not be tested.

Examples of uncertain weights:
- whether a PDA question appears;
- whether pumping is regular or context-free;
- which four of nine named families are selected.

## Phase 2 — define atomic skills and bundled blueprints

Create two layers:

### Atomic skills
Examples:
- DFA design;
- NFA interpretation;
- regex construction;
- pumping witness selection;
- CFG design;
- PDA mechanics;
- closure reasoning.

### Exam blueprints
Blueprints represent instructor-style **question clusters**, not isolated skills.

For example, one blueprint might bundle:
`NFA interpretation -> language description -> regex -> equivalent DFA -> complement`.

This matters because one numbered exam question may test several atomic skills.

Each blueprint should specify:
- skills tested;
- typical subparts;
- difficulty range;
- expected response length;
- source evidence;
- allowed variation;
- validation requirements.

## Phase 3 — encode predictive priors

Do not pretend exact probabilities are known.

Prefer one of these:
- qualitative weights converted to relative sampling weights;
- several scenario models mixed together;
- explicit low/medium/high bands.

A robust default is a scenario mixture:

- **current-semester authority scenario** — driven by direct current evidence;
- **historical-continuity scenario** — preserves instructor/course structural reuse;
- **recency-emphasis scenario** — overweights the most recent lectures/review cues.

Record the scenario mix and all blueprint weights durably.

## Phase 4 — simulate exam blueprints

Simulate large numbers of **blueprints**, not fully written exams.

Typical sizes:
- 100 for a quick preview;
- 1,000 for useful stability;
- 10,000 for a default analytical ensemble.

More samples reduce Monte-Carlo noise but do **not** create new knowledge about the instructor.

Every sampled blueprint must satisfy the hard exam constraints, such as:
- exact question count;
- required mix of construction/proof/conceptual work;
- excluded topics absent;
- plausible instructor-style bundling;
- realistic workload.

## Phase 5 — summarize the ensemble

Measure:

### Marginal inclusion
How often each blueprint family appears.

### Atomic-skill inclusion
How often each underlying skill appears after bundled questions are expanded.

### Conceptual/Q1 recurrence
How often conceptual domains recur.

### Co-occurrence
Which blueprint families or skills repeatedly appear together.

### Position
Only when the instructor historically uses stable question positions.

### Coverage concentration
Find the smallest topic/blueprint set explaining 50%, 80%, and 95% of modeled slot mass.

### Exact-combination diversity
Measure how concentrated or diffuse the plausible exact exam layouts are.

If the most common exact layout is still rare, do not invent one “predicted test.” Use the marginals and clusters instead.

## Phase 6 — materialize representative practice

Do not make the student take thousands of exams.

Use the ensemble to choose a small set of high-information practice exams:

- **centroid/central** — close to the ensemble's center of mass;
- **random plausible** — ordinary draws from the predictive distribution;
- **tail** — lower-frequency but still plausible structures;
- **coverage-maximizing** — adds blueprint combinations not yet practiced;
- **adaptive** — uses mastery weights only;
- **hybrid** — balances predictive realism and remediation.

A typical final preparation window may use:
- 6–10 full timed exams;
- many isolated exam-sized problems;
- multiple short conceptual/T-F sets.

Stop adding full exams when they become redundant and no longer reveal new failure modes.

## Phase 7 — validate every materialized question

Large-N blueprint simulation can be approximate; student-facing questions cannot.

Before showing a generated problem:
- verify it is in scope;
- verify the requested object/proof exists;
- verify language/machine definitions are consistent;
- verify reference solutions;
- verify pumping witnesses and quantifiers;
- verify claimed minimality only when actually established;
- check zero/epsilon/boundary cases;
- ensure workload matches the instructor's exam style.

If validation is uncertain, discard and regenerate.

## Phase 8 — answer-key firewall

Before the attempt:
- show only the exam;
- do not leak intended invariants, witness choices, or solutions;
- do not let grading notes become visible practice hints.

After the attempt:
- grade by subpart;
- distinguish conceptual errors from notation slips;
- record time and confidence when useful;
- persist only meaningful mastery evidence.

## Phase 9 — adaptive mastery loop

After each attempt, update **mastery weights**, not predictive priors.

Increase practice weight for:
- wrong answers;
- slow or uncertain answers;
- method-selection failures;
- guided solutions;
- stale evidence.

Decrease but do not eliminate weight after repeated clean independent transfer.

This loop improves the student without falsely changing the exam forecast.

## Phase 10 — posterior update from new instructor evidence

When new high-authority evidence arrives—especially a review class:

1. preserve the old predictive prior as a named revision;
2. ingest the new evidence;
3. update predictive weights;
4. rerun the ensemble;
5. compare frequency shifts;
6. reallocate practice and cheat-sheet space.

This is a genuine evidence update. Unlike generating more synthetic exams, it can materially change the forecast.

## Cheat-sheet integration

Use the final/post-review ensemble to allocate scarce cheat-sheet space:
- high-frequency recurring concepts get compact lookup protection;
- high-frequency execution families get short recipes;
- student-specific weak skills may get extra examples if space permits;
- explicit exclusions receive no space;
- low-frequency tails may receive only a mnemonic or be omitted.

Do not freeze physical layout before the strongest final review evidence if time allows.

## Interpretation guardrails

Never say:
- “10,000 simulations prove Topic X will be on the exam”;
- “the law of large numbers discovered the instructor's real probabilities”;
- “more synthetic samples equal more instructor evidence.”

Instead say:
- “under the current evidence model, Topic X recurs frequently”;
- “the ensemble exposes the consequences of our assumptions”;
- “new instructor evidence changes the model; more samples only stabilize the model's output.”

## Reuse checklist for another course

To instantiate this method for a new class:

1. ingest current syllabus, lectures, assignments, review material, and instructor communications;
2. identify hard exam invariants and exclusions;
3. collect historical exams only if provenance is known;
4. build atomic skill inventory;
5. define bundled instructor-style blueprints;
6. create predictive priors independent of mastery;
7. simulate 1,000–10,000 constrained blueprints;
8. inspect recurrence/coverage/co-occurrence;
9. take a representative practice series;
10. update mastery separately;
11. ingest final review evidence and rerun;
12. finalize cheat sheet/study allocation from the posterior model.

## Relationship to shared tutoring procedures

This procedure extends `procedures/course_assessment_preparation.md`.

Interactive attempts and mastery updates still route through:
- `procedures/course_study_session.md`;
- `policies/TUTORING_CONTRACT.md`.

The exam-ensemble model predicts assessment structure; it does not replace the tutoring mastery contract.
