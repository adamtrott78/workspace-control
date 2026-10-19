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
- Current stage: `compressed_restart`
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

### Lecture 12 — instructor-note confirmed
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

The transcript file supplied with the L12 notes was byte-identical to L11 (SHA-256 `8048a3ba5b06ef66c8ed8f054ed470b36f16254f79cbe794197eaaa3287002e4`). Do **not** treat it as L12 evidence.

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
