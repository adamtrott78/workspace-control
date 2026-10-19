<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule:

`tasks/active/cis560-exam1-preparation-v1.json`

If this Markdown disagrees with the JSON capsule or verified Git/project evidence, trust the capsule plus verified evidence.

## Task

- ID: `cis560-exam1-preparation-v1`
- Title: CIS 560 Exam 1 Preparation and Cheat-Sheet Build
- Status: `CHECKPOINTED`
- Current stage: `practice_test_factory`
- Exam: **Thursday, October 22, 2026**
- Cheat sheet: **one US Letter page, double-sided**

## Exact current CIS 560 checkpoint

Repository: `adamtrott78/CIS560-AdamTrott`  
Branch: `tutor-framework`  
Checkpoint: `091ba96a013d313c9ae67aada6448e883bf5b77b`

Shared tutoring/workflow behavior remains pinned to:

`workspace-control@0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9`

## Source state

### Lecture 11 — resolved
- raw transcript is durable at `sources/lectures/L11_TRANSCRIPT_RAW.md`;
- live notes, board-photo record, CFL pumping handout, and instructor Section 2.3 note remain source-separated;
- Q1/Q2-Q5/75-minute format guidance is transcript-confirmed;
- CYK is conceptually exam-relevant/required reading;
- **complete CYK procedure is explicitly not tested**.

### Lecture 12 — transcript reconciled
Durable:
- `sources/instructor/L12_NOTES_2026-10-15_USER_PROVIDED.md`
- `course/lectures/L12.md`

Key authority:
- finish Section 2.3;
- **Section 2.4 is not required**;
- non-CFL pumping proof is explicitly re-emphasized;
- `REG ⊊ CFL`;
- DFA/NFA→PDA;
- regular closure properties;
- next class = quick midterm review.

Raw genuine transcript: `sources/lectures/L12_TRANSCRIPT_RAW.md` (SHA-256 `5dee87e3d2eafa6692239356f36e5bdb4de473dd3e42394d9d16515aff8f8902`). The earlier duplicate-L11 attachment remains excluded from L12 provenance.

## Exam architecture

- Q1 = True/False.
- Q2–Q5 = four short homework/class-example-style problems.
- Named candidate family remains broader than four slots:
  DFA, NFA, regex, CFG, PDA, RL show-pumping, CFL show-pumping, prove nonregular, prove non-CFL.
- Do not claim all named families appear.
- 75 minutes; compact correctness over long prose.

## High-value current rules

### Pumping property
- RL: one legal `xyz` partition + conditions.
- CFL: one legal `uvxyz` partition + conditions.
- HW-length explanatory prose is not needed on the exam.

### Prove not regular / not CFL
- arbitrary pumping length `p`;
- choose a p-dependent witness in the language with length >= p;
- cover every legal split/placement;
- one bad partition is never enough;
- choose pump direction strategically;
- contradiction.

### Lecture 12 non-CFL shorthand
1. Find the correct counterexample/witness.
2. Show it cannot be pumped **no matter how it is divided into five parts**.

## Behavioral evidence from restart

Persisted in `study/MASTERY_LOG.md`:
- CFG ordered-count transfer: independent;
- CFG palindrome/outside-in transfer: independent;
- PDA phase/stack mechanics: independent on a simple family;
- regular pumping witness selection: independent;
- CFL non-CFL proof: witness + exhaustive placement structure student-derived; compact presentation guided.

Remaining comparatively higher-risk construction family:
- NFA/regex/HW1-derived conversion work.

## Cheat-sheet reweighting

Protect heavily:
- Q1 distinction/trap box;
- all short-problem recipes;
- non-CFL pumping proof skeleton;
- regular closure;
- `REG ⊊ CFL`;
- DFA/NFA→PDA;
- CYK concept only.

Exclude:
- Section 2.4;
- full CFG→CNF conversion procedure;
- proofs of Lemmas 2.21 and 2.27;
- complete CYK table procedure.

Do not freeze final space until after the October 20 review.

## Next safe action

If the user supplies the **2024 Exam 1**, ingest it next as historical predictive evidence and compare it against current Fall 2026 authority.

If not, run one fresh **NFA/regex** transfer diagnostic.

Then:
1. ingest October 20 review;
2. reweight/finalize cheat sheet;
3. run timed mixed mini-midterm October 21.


## Practice-test factory

Durable factory root:

`study/exam1/practice_factory/`

Files:
- `README.md` — usage/modes;
- `FACTORY_SPEC.md` — format, authority, freshness, validation, grading/adaptation;
- `BLUEPRINTS.md` — Xu-style Q1 and Q2–Q5 families;
- `FACTORY_STATE.json` — current mastery weights and generated-variant ledger;
- `TEST_TEMPLATE.md` — 25-point / 75-minute shell.

Default:
- Q1 = five True/False items;
- Q2–Q5 = four 5-point short problems;
- questions may bundle multiple related skills;
- current-semester authority wins over 2024 historical evidence;
- validate every generated item;
- do not expose answer keys before the student's attempt.

Current weakness reweight:
- emphasize fresh NFA/regex/conversion transfer until independently demonstrated.

After each test:
- grade by subpart;
- update meaningful mastery evidence;
- reweight factory state;
- avoid reused variant IDs.

October 20 review remains the final weighting event.
