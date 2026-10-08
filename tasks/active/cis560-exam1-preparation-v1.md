<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule:

`tasks/active/cis560-exam1-preparation-v1.json`

If this Markdown disagrees with the JSON capsule or verified Git/project evidence, trust the capsule plus verified evidence.

## Task

- ID: `cis560-exam1-preparation-v1`
- Title: CIS 560 Exam 1 Preparation and Cheat-Sheet Build
- Status: CHECKPOINTED
- Current stage: `pre_milcom_preservation`
- Default tutoring semantics: **EXAM_READINESS / MASTERY_RECOVERY**
- Exam: **Thursday, October 22, 2026**
- Cheat sheet: **one US Letter page, double-sided**

## Exact CIS 560 checkpoint

Repository:
`adamtrott78/CIS560-AdamTrott`

Branch:
`tutor-framework`

Required checkpoint:
`3e5906ca572f47272ac14a4d4ac2ed4ae9eb0122`

This checkpoint already includes:
- explicit Exam 1 invariants;
- all named Q2–Q5 candidate families;
- concrete current-semester practice anchors under each family;
- updated study plan after HW3 completion;
- Q1/Q2–Q5 cheat-sheet architecture;
- reconciled post-Lecture-11 timeline;
- durable slide coverage L1–L10;
- current handout inventory;
- Lecture 11 live notes, board evidence, and CFL pumping handout.

CIS560 shared tutoring/workflow behavior remains pinned to:

`workspace-control@0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9`

## Cold-start routing

Start from the CIS560 root route:

1. `README.md`
2. `COURSE.md`
3. `study/exam1/README.md`
4. `study/exam1/EXAM_INVARIANTS.md`
5. `study/exam1/STUDY_PLAN.md`
6. `study/exam1/CHEATSHEET_CANDIDATES.md`
7. `study/exam1/INSTRUCTOR_EMPHASIS.md`
8. `study/exam1/QUESTION_BANK.md`
9. Read homework learning records only as needed for behavioral prioritization:
   - `homework/hw01/LEARNING.md`
   - `homework/hw02/LEARNING.md`
   - `homework/hw03/LEARNING.md`

Do **not** recursively reread/reconstruct the entire course at startup.

Use source indexes only when source-level detail is needed:
- `course/LECTURES.md`
- `sources/instructor/SLIDE_DECK_INDEX.md`
- `sources/instructor/MATERIAL_INVENTORY.md`
- `sources/instructor/handouts/2026_HANDOUT_INDEX.md`

## October 8 exam invariants — preserve these

These are direct current-semester Xu guidance captured live. Exact transcript wording is still pending, but the substance is high confidence.

### Exam structure

- **Q1 = True/False.**
- **Q2–Q5 = short problems similar to homework problems and class examples.**
- Exam length: **75 minutes**.
- Xu said there are **no long-response questions** beyond these short problem forms.
- He does not expect extended writing / use of the back for long responses.

### Full Q2–Q5 candidate family Xu named

Preserve **all** of these:

1. design a simple **DFA**;
2. design a simple **NFA**;
3. **regular-expression** work;
4. design a **CFG**;
5. design a **PDA**;
6. show the **regular-language pumping property**;
7. show the **context-free-language pumping property**;
8. use the pumping lemma to prove a language is **not regular**;
9. use the CFL pumping lemma to prove a language is **not context free**.

There are nine named families and only four Q2–Q5 slots.

Therefore:
- this is the candidate pool;
- **do not claim every family will appear**;
- exact four selections remain unknown.

## Pumping answer-format invariants

### Show the pumping property

Xu said the exam answer does **not** require HW3-length prose.

For RL:
- give legal `s=xyz`;
- verify:
  - `xy^iz ∈ L` for every `i>=0`;
  - `|y|>0`;
  - `|xy|<=p`.

For CFL:
- give legal `s=uvxyz`;
- verify:
  - `uv^i x y^i z ∈ L` for every `i>=0`;
  - `|vy|>0`;
  - `|vxy|<=p`.

For a show-property problem, **one valid legal partition is enough**.

### Prove not regular / not CFL

Different quantifier burden:

- assume class membership;
- let `p` be arbitrary pumping length;
- choose a useful **p-dependent witness**;
- consider **every legal split/placement case**;
- choose pump exponent strategically;
- force pumped string outside the language;
- contradiction.

One bad split is not enough.

## Xu's stated readiness criterion

He told the class to:
- redo homework problems;
- redo class examples;
- solve them **independently without looking at solutions**.

Working interpretation:

> If Adam can independently solve the homework/class-example families without solutions, he should be able to do the exam.

This is the primary Q2–Q5 behavioral test.

Do not substitute passive rereading.

## Concrete current-semester practice corpus

These are anchors, not predictions of verbatim exam languages.

### DFA
- ending in 1;
- odd number of 0s;
- contains `001`;
- ends in `00`;
- complement: does not end in `00`;
- starts and ends with the same symbol;
- HW1 DFA construction work.

### NFA
- ends in `00`;
- contains `011`;
- contains `101` or `11`;
- union/concatenation/star constructions;
- HW1 NFA construction work.

### Regex
- equivalent regexes for odd number of 0s;
- precedence `* > concat > union`;
- epsilon/empty-language identities;
- HW1 regex→NFA;
- GNFA state elimination.

### CFG
Xu's three live design scenarios:
1. union;
2. regular target via DFA/NFA→CFG;
3. recursive related counts/positions.

Current examples:
- `0^n1^n`;
- palindromes;
- `Sigma*`;
- contains a fixed substring;
- HW3 3-1 avoiding `110`;
- HW3 3-1 equal numbers of a's/b's.

### PDA
- Lecture 10 `{a^n b^n}`;
- Lecture 10 nondeterministic OR matching example;
- HW3 3-3 `{a^i b^j c^k | i=j or j=k}`.

### RL pumping property
- Lecture 7 `L=a(bb)*a`, minimum pumping length `p=3`.

### CFL pumping property
- Lecture 11 `L={w | #a(w)=#b(w)}`;
- fixed-p examples `aabb`, `abab`;
- Lecture 11 parse-tree pumping intuition for `{0^n#1^n}`;
- HW3 3-4 pumpability problems.

### Prove not regular
- canonical `{0^n1^n}`;
- equal number of 0s and 1s;
- `{a^m b^n | m>n}`;
- HW2 pumping problems.

### Prove not CFL
- Lecture 11 board proof `{a^n b^n c^n}`;
- Fall-2026 handout `{a^i b^j c^k | 0<=i<=j<=k}`;
- Fall-2026 handout `{ww | w∈{0,1}*}`.

## Q1 True/False protection

High-value compact distinctions include:

- DFA: exactly one outgoing transition per state/input symbol.
- NFA: one accepting path suffices; reject only if all paths fail/reject.
- DFA and NFA have equal language-recognition power.
- General PDA is nondeterministic; **DPDA is strictly weaker than PDA**.
- regular iff DFA-recognizable iff NFA-recognizable iff regex-describable.
- CFL iff CFG-generable iff PDA-recognizable.
- pumping lemma implication is **one-way**:
  - regular -> RL pumping property;
  - CFL -> CFL pumping property;
  - converse is not licensed.
- regular languages closed under union, concat, star, complement, intersection.
- only union/concat/star are called the three **regular operations**.
- distinguish `epsilon`, `emptyset`, and `{epsilon}`.
- ambiguous string vs ambiguous CFG vs inherently ambiguous language.
- CNF: `A->BC` or `A->a`, with special start/epsilon rule.
- failure to find DFA/regex is not proof of nonregularity.
- failure to find CFG/PDA is not proof of non-context-freeness.
- iff statements require both directions.

Explicit exclusions:
- full CFG→CNF conversion procedure is **not required on the exam**;
- proofs of Lemmas 2.21 and 2.27 are **not required**.

## CYK status — do not overstate

As of end of Lecture 11:
- syllabus Week 7 topic;
- Lecture 10 note says **required reading**;
- current Canvas handout is distributed and durably summarized;
- user explicitly clarified Xu had **not yet substantively taught CYK live**.

Do not label CYK live-taught until Lecture 11 transcript / Lecture 12 / review establishes it.

Current preparation status:
- keep a compact executable CYK box on the candidate sheet;
- final weight remains pending.

## Cheat-sheet architecture

Constraint:
- **one US Letter page, double-sided.**

Functional design:

### Region 1 — Q1 T/F protection
Dense theorem/definition/trap statements.

### Region 2 — Q2–Q5 execution recipes
Compact boxes for every named family:
- DFA;
- NFA;
- regex/GNFA;
- CFG;
- PDA;
- RL show-property;
- RL nonregular proof;
- CFL show-property;
- CFL non-CFL proof;
- CYK until review decides final weight.

Space rule:
- exact conditions;
- quantifier traps;
- recipes;
- proof skeletons;
- compact formulas.

Avoid:
- long English explanations;
- polished homework prose;
- full explicitly excluded proofs;
- large solved examples with no reusable pattern.

Do not freeze final density/layout until after the October 20 review.

## Behavioral evidence that should drive practice

### HW1
- DFA state design has independent evidence.
- complement, NFA concatenation/star, reversal proof, regex→NFA remain guided and deserve fresh transfer if relevant.

### HW2
Important durable evidence includes:
- pumping/nonregularity practice;
- witness selection was a meaningful weakness;
- closure proof and minimum-pumping work;
- CFG derivation/language characterization.

Read `homework/hw02/LEARNING.md` for exact states before claiming mastery.

### HW3 — already complete
Do **not** treat it as unfinished.

Current learning evidence:
- CFL pumpability: strong independent evidence, but still needs delayed/fresh transfer for exam-ready.
- CNF 2.26 counting proof: strong independent reasoning after a production-form reminder; needs delayed transfer.
- CFG avoiding `110`: independent.
- CFG equal #a/#b: required substantive structural guidance -> fresh transfer priority.
- PDA core branch/stack strategy: student-derived, but full JFLAP mechanics/read-pop-push/bottom-marker/zero-count handling required guidance -> fresh transfer priority.
- final HW3 document/PDF and PDA artifact were validated; artifact completion does not imply mastery.

## Pre-MILCOM priority

HW3 is done. Do **not** burn Friday/Saturday simply re-completing it.

Before Sunday travel:
1. cold CFG design transfer;
2. cold PDA transfer;
3. regular pumping witness-selection transfer;
4. fresh CFL non-CFL case-analysis transfer;
5. at least one DFA/NFA/regex transfer;
6. refine cheat-sheet skeleton;
7. create a compact restart packet.

Balance this against MILCOM preparation.

## Hard schedule constraints

- Sunday night Oct. 11: fly to MILCOM.
- Wednesday during conference: present research paper.
- Thursday night Oct. 15: fly home.
- Professor explicitly advised putting academics on hold for MILCOM.
- **No planned substantive CIS 560 study Oct. 11–15.**
- Friday Oct. 16–Sunday Oct. 18: MTH 602-only study block.
- Monday Oct. 19, 11:00 AM: MTH 602 Midterm 1.
- CIS 560 intensive preparation resumes after MTH on Oct. 19.
- Tuesday Oct. 20: expected Xu review class.
- Thursday Oct. 22: CIS 560 midterm.

The plan must work without academic maintenance during the blackout.

## Remaining source events

### Lecture 11 transcript
When available:
- ingest it;
- verify exact exam wording;
- resolve exactly what Xu said about CYK;
- reconcile pumping examples/case language;
- preserve live-note provenance rather than overwriting it.

### October 15 Lecture 12
Expected final new-content class under the user's long-running experience with Xu.
User may miss it because of MILCOM/travel.
Ingest it immediately after MTH when appropriate.

### October 20 review
Treat as the strongest final **weighting/prioritization** source.

Capture:
- explicit on/off-exam statements;
- examples/problems revisited;
- all “important/remember/know how to” signals;
- any further question-format detail.

Use review to tune an already-complete scope model, not to build scope from scratch.

## Historical 2019 evidence

Useful for stable-pattern prediction only.

Known continuity:
- 2019/current syllabus pre-midterm schedule highly similar;
- HW1 nearly verbatim;
- HW2 heavily reused;
- HW3 selectively reused:
  - CFG design reused;
  - PDA problem reused;
  - Sipser 2.26 retained;
  - full old CNF conversion removed;
  - old CYK homework removed;
  - current pumping block redesigned.

Current-semester evidence always wins.

## Source/provenance rules

- Quote only actual/near-verbatim source wording.
- Keep paraphrases unquoted.
- Do not turn transcript paraphrases into fake quotes.
- Slides indicate prepared coverage, not automatically spoken emphasis.
- Handout distribution indicates intentional course supply, not automatically live teaching.
- Large PDFs/images may not be in Git; use indexes/hashes and request originals when exact visuals matter.
- Never invent missing board/diagram detail.

## Next safe action

Recover the durable state above.

If the user supplies the Lecture 11 transcript, ingest/reconcile it first.

Otherwise continue **pre-MILCOM exam preservation**, starting with one targeted cold-transfer diagnostic from a high-risk guided Q2–Q5 family rather than a broad prerequisite quiz.

Good default first diagnostic:
- a fresh CFG or PDA design problem that is not copied from HW3;
- one substantive question at a time;
- minimal scaffolding;
- update durable evidence only at meaningful boundaries.
