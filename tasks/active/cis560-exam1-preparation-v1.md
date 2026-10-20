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
- Current stage: `cheat_sheet_build`
- Exam: **Thursday, October 22, 2026**
- Cheat sheet: **one US Letter page, double-sided**

## Exact current CIS 560 checkpoint

Repository: `adamtrott78/CIS560-AdamTrott`  
Branch: `tutor-framework`  
Checkpoint: `784cdf9625257dee88ce70d832b0109578c4f248`

Shared tutoring/workflow behavior remains pinned to:

`workspace-control@0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9`

## October 20 final review — ingested

Authoritative live-note source:

`sources/instructor/L13_MIDTERM_REVIEW_2026-10-20_USER_PROVIDED.md`

This is now the strongest final pre-exam weighting event.

### Explicitly reinforced
- DFA/NFA definitions, semantics, equivalence, simple design.
- Given NFA: understand its language and design an equivalent DFA.
- machine -> English description -> regex -> DFA -> complement workflow.
- DFA complement by swapping accepting/nonaccepting states; not directly for NFA.
- regex/automata equivalence; **regex -> NFA required**.
- regular closure and one-way directionality.
- RL pumping directionality, pumpability, minimum/sufficient pumping length, nonregular proofs.
- CFG/string ambiguity; CNF recognition.
- CYK concept = membership.
- CFL pumpability using exact `s=uvxyz`.
- PDA design; nondeterministic OR branching.
- NFA as zero-stack PDA; DPDA < NPDA.

### Explicitly excluded / de-emphasized
- **GNFA procedure/state elimination: no exam question.**
- **full CYK execution/table: not on exam.**
- **inherent/language ambiguity: not on exam.**
- full CFG -> CNF conversion remains excluded.
- Section 2.4 remains excluded.
- formal NFA -> DFA subset-construction procedure is not itself required, although equivalent-DFA design remains required.

One CFG undecidability comment in the live notes was incomplete; the exact decision problem is deliberately left unresolved rather than inferred.

## Post-review predictive posterior

Files:
- `study/exam1/practice_factory/PREDICTIVE_PRIORS_POST_REVIEW.json`
- `study/exam1/practice_factory/ENSEMBLE_POST_REVIEW_10K.md`

Simulation:
- 10,000 accepted blueprints
- seed `5602026`
- 14,518 candidate draws

Highest modeled Q2–Q5 families:
1. CFL show-pumpability — 44.49%
2. NFA -> language -> regex -> DFA -> complement — 38.97%
3. RL pumping prove nonregular — 36.04%
4. DFA/NFA -> CFG mixed — 33.46%
5. RL pumpability / minimum pumping length — 33.08%
6. regex -> NFA — 30.99%
7. prove non-CFL — 29.01%

Largest post-review shifts:
- regex -> NFA: **up**
- RL pumpability/minimum p: **up**
- grammar ambiguity/CNF: **up**
- non-CFL proof: **down but still live**
- GNFA/Myhill bundled secondary: **near-zero**

Interpret frequencies as model-implied recurrence, not literal probabilities.

## Behavioral state

Persisted in `study/MASTERY_LOG.md`.

Strong/recent:
- CFG ordered-count and outside-in/palindrome patterns.
- PDA push/switch/pop design on fresh families.
- regular nonregular pumping witness selection.
- non-CFL witness + five placement-family structure.
- CFL closure facts stabilized after repeated drills.
- CNF recognition.
- NFA/regex notation improved on fresh transfer.

Remaining execution risk:
- precise DFA state invariants under fresh automata conversion tasks;
- regular pumping **show-property / minimum-p** quantifiers need continued short transfer;
- regex -> NFA deserves explicit fresh practice because Xu named it in final review.

## Final cheat-sheet allocation

Owner:
`study/exam1/CHEATSHEET_CANDIDATES.md`

Must protect:
- DFA/NFA semantics and construction.
- NFA acceptance: exists accepting path.
- DFA complement guard.
- regex equivalence + regex -> NFA recipe.
- `(a|b)*` vs `(ab)*`.
- regular closure + directionality.
- RL pumping: one-way lemma, show-property vs nonregular proof, minimum p.
- CFG/string ambiguity.
- CNF forms.
- CYK membership concept only.
- CFL `uvxyz` pumpability conditions.
- PDA design + nondeterministic OR.
- reusable CFG patterns such as `T->0T|1T|epsilon`.

Do **not** allocate procedure space to:
GNFA elimination, full CYK, full CNF conversion, inherent ambiguity, Section 2.4, or formal subset-construction memorization.

## Next safe action

1. Build/render/visually QA the final two-sided cheat sheet.
2. Then run a short **hybrid posterior-guided** practice set:
   - NFA/DFA/regex/complement;
   - regex -> NFA;
   - RL show-pumpability / minimum p / nonregular proof;
   - CFL show-pumpability;
   - one CFG/PDA mixed check if needed.
3. Keep one non-CFL proof refresh for coverage without overinvesting.
4. Finish with a timed readiness check on October 21.

