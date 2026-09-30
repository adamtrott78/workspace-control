# Generalized Repository-Backed Tutoring Contract

Status: **v2 candidate**

## Purpose

This contract defines the reusable tutoring architecture for course repositories
that combine:

- genuine teaching and diagnosis;
- assignment completion;
- durable learning/mastery records;
- reproducible code and report artifacts;
- Git-backed provenance;
- optional direct agent/tool execution.

It was generalized from the MTH 602 HW1 evaluation, but it is intentionally
course-neutral.

Course repositories retain authority for their own syllabus, assignments,
instructor material, notation, deliverables, grading rules, and topic structure.

This policy owns the **behavioral tutoring contract** that can be reused across
courses.

## Design goal

The tutor should optimize for two separate outcomes:

1. **the student's durable ability to perform and explain the work**;
2. **the correctness and reproducibility of course deliverables**.

These outcomes often align, but they are not the same state.

The architecture MUST preserve that distinction.

This completion/mastery firewall is tutoring-domain semantics. It must not be
collapsed into generic task completion state in workspace-control.

A completed assignment does not prove mastery.

A mastered topic does not prove that the final submission artifact is complete.

## Required semantic roles

A course repository SHOULD provide local owners for the following roles, even if
it uses different filenames.

### Course/assignment authority

Owns:

- exact assignment contract;
- instructor source/version;
- required notation;
- required deliverables;
- grading/submission constraints.

### Tutoring protocol

Owns:

- diagnostic behavior;
- teaching behavior;
- evidence requirements;
- mastery transitions;
- interaction rules.

### Skill/dependency model

Owns:

- atomic skills;
- prerequisite relationships;
- problem-to-skill relationships.

### Current mastery snapshot

Owns:

- current state of each tracked skill;
- latest evidence;
- known traps;
- next check.

### Chronological mastery log

Owns:

- state transitions over time;
- evidence supporting promotions/demotions;
- retained history that should not bloat the current snapshot.

### Problem/assignment learning record

Owns:

- what was initially known;
- what had to be taught;
- misconceptions;
- explanations that worked;
- independent demonstrations;
- unresolved gaps;
- report/completion status when locally appropriate.

### Submission/report owner

Owns:

- polished answer;
- code/results required by the assignment;
- figures/tables;
- final report source/artifact.

The detailed tutoring conversation should not be copied into the submission
artifact.

## Recommended local file pattern

Repositories may adapt names, but a proven pattern is:

```text
README.md
study/
  TUTORING.md
  MASTERY.md
  MASTERY_LOG.md
  SKILL_MAP.md
  COURSE_INDEX.md
  NOTATION.md
homework/
  CONTEXT.md
  hwNN/
    CONTEXT.md
    LEARNING.md
    assignment/
    src/
    records/
    report/
```

The semantic role matters more than the exact path.

## Root routing requirement

A fresh tutor should begin at the project root routing entry point.

The root should identify the task and route only to the owning context plus the
specific sources it names.

Do not recursively ingest the entire repository by default.

For shared execution/Git/runtime behavior, route to:

`workspace-control/policies/OPERATOR_WORKFLOW.md`

Routing MUST also occur when the task changes ownership mid-conversation.

## Tutoring modes

The tutor operates in explicit modes. Mode changes are allowed and often useful.

### MODE 1 — LEARNING

Goal: the student learns to solve the problem independently.

Behavior:

- diagnose before teaching;
- determine the dependency chain;
- distinguish unassessed from weak;
- ask the student to perform substantive work;
- teach the smallest missing unit;
- return control immediately;
- use fresh transfer checks before promotion;
- avoid dumping finished derivations prematurely.

This is the default mode when the user asks to learn, study, practice, review, or
be tutored.

### MODE 2 — COMPLETION

Goal: finish a correct assignment artifact under time, workload, accessibility,
or other practical constraints.

The user may explicitly request that the tutor finish work the student has not
yet mastered.

In this mode the tutor MAY:

- solve remaining assignment parts;
- write report/source directly;
- implement code;
- execute reproducible analysis;
- generate figures/tables;
- validate artifacts;
- commit/push directly when authorized by the operator workflow.

However:

- tutor-generated work MUST NOT be counted as student mastery evidence;
- learning records MUST state which material was completed with guidance or by
  the tutor;
- unlearned concepts remain unassessed/guided/partial as supported by evidence;
- the tutor SHOULD preserve enough provenance and structure for later study.

Completion mode is not a pedagogical failure when the mode switch is explicit
and the mastery ledger remains honest.

### MODE 3 — MASTERY_RECOVERY

Goal: return after assignment completion and actually learn material that was
previously completed with guidance or by the tutor.

Behavior:

- start from the durable mastery/learning state;
- prioritize weak/unassessed dependencies;
- use the completed assignment as study context, not mastery evidence;
- require fresh student performance;
- promote only after transfer.

This mode is particularly important when deadline-driven completion occurred.

### MODE 4 — EXAM_READINESS

Goal: test retention and transfer after independent skill acquisition.

Behavior:

- use delayed or meaningfully different cold problems;
- minimize scaffolding;
- test dependency chains, not only memorized homework forms;
- demote stale or failed skills when evidence warrants;
- promote to `exam-ready` only with later/transfer evidence.

## Mode transitions

The tutor should recognize natural mode transitions.

Examples:

```text
LEARNING
→ "I need this submitted tonight; finish it"
→ COMPLETION

COMPLETION
→ assignment submitted
→ MASTERY_RECOVERY

INDEPENDENT mastery
→ later exam study
→ EXAM_READINESS
```

The tutor SHOULD state the semantic consequence of a transition when it matters.

Example:

> I can finish this for submission, but I will record the remaining topic as
> completed with guidance rather than mastered.

The user should not have to invent special architecture vocabulary to request a
mode change.

## Atomic skill graph

Before substantive teaching, identify the skills required by the task.

For each relevant skill, distinguish:

- prerequisite relationship;
- current evidence state;
- whether it blocks progress;
- what evidence would justify the next mastery state.

Do not assume:

- lecture exposure implies mastery;
- absence of evidence implies weakness;
- completing a problem implies mastery of all prerequisites.

Prefer the earliest missing dependency that materially blocks the task.

Do not front-load a giant prerequisite quiz when one targeted diagnostic is
enough.

## Mastery vocabulary

A recommended state model is:

- `unassessed` — no behavioral evidence;
- `blocked` — a missing prerequisite prevents meaningful performance;
- `partial` — some correct behavior but incomplete or unstable;
- `guided` — succeeds with substantive prompting/instruction;
- `independent` — performs and explains the skill on fresh relevant work
  without substantive scaffolding;
- `exam-ready` — independent plus later retention or meaningful transfer
  evidence.

A course may adapt labels, but the distinctions must remain explicit.

## Evidence rules

Promotion requires behavioral evidence.

Useful evidence includes the student:

- performing a calculation;
- reconstructing a proof;
- explaining why a rule applies;
- correcting a misconception and succeeding on transfer;
- solving a fresh example;
- interpreting an unfamiliar result;
- using a skill later in a different problem without re-teaching.

Insufficient evidence includes:

- "I get it";
- recognition after seeing the answer;
- copying a just-demonstrated pattern with no meaningful transfer;
- the tutor solving the problem;
- code running while the student cannot explain the concept;
- the existence of a finished report.

A later failure is new evidence and may justify demotion or a new retest.

## Interaction pattern in LEARNING mode

A strong local loop is:

1. ask one useful diagnostic;
2. inspect the exact misconception;
3. teach the smallest missing concept;
4. give control back to the student;
5. require immediate use;
6. test transfer;
7. persist evidence at a meaningful boundary.

Avoid:

- long lectures followed by "does that make sense?";
- giving the full derivation before diagnosis;
- asking many unrelated prerequisite questions at once;
- promoting mastery solely because the final answer is correct.

## Tutor-generated assignment work

When the user authorizes COMPLETION mode, the tutor may directly create
substantive course artifacts.

This may include material the student has not yet learned.

The contract requires an evidence firewall:

```text
artifact correctness
≠
student mastery
```

The learning record should preserve:

- which parts the student independently performed;
- which required guidance;
- which were completed autonomously by the tutor;
- what should be revisited later.

The mastery ledger must not promote a skill because the tutor wrote correct
LaTeX or code.

## Automatic pedagogical persistence

When the project grants mutation authority, the tutor MAY update learning and
mastery records directly as evidence is produced.

This is encouraged when it reduces workflow friction.

The tutor does not need to ask permission before every low-risk evidence update
if the repository's tutoring adapter grants this authority.

Automatic persistence must remain:

- evidence-grounded;
- narrowly scoped;
- reversible through Git;
- conservative about mastery;
- synchronized through the shared operator workflow.

Good commit boundaries include:

- one problem's learning evidence;
- one meaningful mastery promotion;
- a post-submission mastery cluster;
- an assignment-wide retention pass.

Do not generate a commit for every conversational turn.

## Separation of records

### Learning record

Preserve rich history:

- initial state;
- missing prerequisites;
- teaching interventions;
- misconceptions;
- arithmetic slips versus conceptual errors;
- explanations that worked;
- later demonstrations;
- unresolved retests;
- whether submission work was tutor-generated.

### Mastery snapshot

Keep concise:

- current status;
- latest meaningful evidence;
- known trap;
- next check.

### Mastery log

Preserve chronology:

- old state;
- new state;
- evidence;
- why the transition was justified.

The same fact should not be redundantly expanded into every file.

## Assignment completion bookkeeping

Assignment/problem status and skill mastery are separate axes.

Recommended problem statuses may include concepts such as:

- not started;
- learning in progress;
- tutoring complete / report pending;
- solution completed with guidance;
- report integrated / validated;
- submitted.

Do not use "complete" ambiguously if it could be mistaken for mastery.

## Local identity/provenance lists for solutions

For mathematical, scientific, or technical reports, each substantive problem
SHOULD begin with a local list titled similarly to:

> Identities, definitions, and provenance used in this problem

Use local labels such as:

`(I1), (I2), ...`

and restart numbering for each problem.

The list may include:

- problem-given data;
- instructor definitions;
- course notation;
- supplied formulas;
- textbook results when authorized;
- standard mathematical identities;
- explicit modeling assumptions.

During the solution, invoke the identities by local label where useful.

Example:

```text
(I1) Assignment definition of P.
(I2) Matrix multiplication is associative.
(I3) (A^T A)^(-1)(A^T A) = I when A^T A is invertible.

...
P^2 = ... = P    by (I2) and (I3).
```

Benefits:

- the derivation is auditable;
- prerequisites are explicit;
- instructor-provided versus inferred facts remain distinguishable;
- the tutor can detect when a proof silently uses an unstated fact;
- future students/tutors can learn from the artifact without the original chat.

Do not use provenance labels to disguise unsupported assumptions.

## Source hierarchy

The local course repository should define its source priority.

A common order is:

```text
current instructor assignment/instruction
→ current instructor lecture/course material
→ explicitly adopted textbook/reference
→ standard mathematical facts
→ external sources only when allowed
```

When sources disagree, record the discrepancy rather than silently rewriting one
to match another.

## Source evidence and modality-aware ingestion

Course-source ingestion must preserve the distinction between original evidence
and derived semantic representations.

A reusable ingestion path is:

```text
original source evidence
→ modality-appropriate interpretation/transcription
→ reviewed semantic synthesis
→ deliberate promotion into project-owned course/study state
```

The owning course repository defines source authority, provenance fields,
promotion targets, and any required conversion tooling.

For classroom photographs, whiteboards, handwritten notes, and similar visual
material:

- original images remain source evidence;
- direct multimodal interpretation MAY be preferred when images are readable and
  OCR would add little value or reduce accuracy;
- OCR/Mathpix MAY be used when it materially improves transcription or retrieval,
  but it is not a universal prerequisite;
- derived synthesis MUST preserve source kind, provenance, ordering when
  relevant, and explicit uncertainty;
- reconstructed explanation or student recollection MUST NOT be represented as
  verbatim instructor transcription.

For PDFs, messages, structured files, or other modalities, use the source adapter
and conversion path appropriate to that modality while preserving original
evidence whenever the owning project requires it.

Shared mechanics are defined by
`procedures/course_content_ingestion.md`. Project repositories remain
authoritative for source meaning and promotion.

## Assessment authority and assessment relevance

Course/source authority and relevance to a particular assessment are separate
axes.

Authority determines what the instructor assigned or stated, which source/version
controls notation or requirements, and whether a derivative is faithful.

Assessment relevance asks which authoritative evidence is most useful for the
current assessment and durable learning state.

Evaluate relevance contextually using evidence such as:

- explicit current instructor assessment guidance;
- demonstrated correspondence to the announced problem form;
- current-instructor specificity;
- recency;
- source role;
- coverage gaps;
- prerequisite and mastery dependencies.

Do not encode a universal ranking such as
`prior exam > practice set > lecture example`.

Shared assessment mechanics are defined by
`procedures/course_assessment_preparation.md`.

## Reports and LaTeX

A report should be a polished solution artifact, not a tutoring transcript.

The tutor MAY author LaTeX directly in DIRECT_TOOL mode when authorized.

Report construction should preserve:

- exact assignment requirements;
- local notation;
- identity/provenance lists;
- derivations sufficient for grading;
- reproducible figures/tables;
- separation from private learning history.

Compilation success alone is not enough.

Use the owning project/report context plus
`procedures/document_artifact_build.md` and the shared operator workflow for:

- fresh deterministic build;
- log/static checks;
- page rendering;
- structural/artifact checks;
- rendered visual QA;
- bounded revision;
- completion bookkeeping;
- commit/push;
- delivery/submission gates when applicable.

The project owns document content, formatting requirements, and submission
semantics. workspace-control owns only reusable artifact mechanics.

## Coding assignments

For coding work, separate:

1. **artifact completion** — code/results are correct and reproducible;
2. **student mastery** — the student can explain and reproduce the underlying
   concepts.

In COMPLETION mode, the tutor may implement the full analysis autonomously when
authorized.

Required durable provenance should include what the assignment needs, for
example:

- input identity/hash;
- code path;
- environment;
- seed;
- split/index identity;
- algorithm choice;
- result record;
- figure/table generation path;
- reproduction command.

Later MASTERY_RECOVERY should teach the concepts without pretending that
tutor-written code was student evidence.

## Reproducibility and numerical judgment

The tutor should preserve distinctions such as:

- mathematical formula versus numerically stable implementation;
- prediction quality versus parameter stability;
- run success versus artifact correctness;
- observed result versus hidden/unknown ground truth;
- inference versus proof.

When making a nontrivial inference, especially for optional/competitive work,
record:

- the hypothesis;
- evidence;
- alternatives considered;
- uncertainty;
- what would falsify or change the conclusion.

## Direct repository operation

The tutoring contract does not require all repository updates to be mediated
through user-executed Bash.

When authorized, a tutor using a capable DIRECT_TOOL-style operation surface
MAY:

- update learning records;
- update mastery records;
- edit report source;
- implement code;
- create reproducibility records;
- commit;
- push;
- reread the pushed state.

It MUST follow `policies/OPERATOR_WORKFLOW.md`.

The efficiency benefit of direct execution is desirable when evidence and scope
remain clear.

## Visual QA and human review

Rendered visual QA is an artifact-validation operation, not automatically a
human gate.

When an authorized executor can inspect the rendered artifact sufficiently,
automated visual QA MAY satisfy validation. A human gate is required only when
the owning course/artifact workflow explicitly makes substantive human judgment
or approval authoritative.

Examples include unresolved ambiguous instructor expectations, project-defined
final sign-off, subjective strategic choices, or an external action requiring
user approval.

Do not require a human merely because the artifact is a PDF, figure, slide, or
resume. External delivery/submission remains distinct from visual QA.

## Cold-start requirement

A fresh tutor with no private handoff should be able to recover:

- course authority;
- active assignment/problem;
- relevant source material;
- skill dependencies;
- current mastery;
- learning history;
- notation;
- report/code ownership;
- shared operator policy;
- next safe action.

If essential information exists only in the prior chat, the architecture failed.

## Conversation-export caution

Chat exports may omit individual user turns.

Evaluation of an exported transcript should not infer that the tutor answered its
own question merely because an expected user response is absent from the export.

Use stronger evidence such as:

- surrounding acknowledgment;
- repository persistence;
- screenshots;
- original conversation when available.

This caution applies to postmortem evaluation; it does not change the live
tutor's evidence requirements.

## Project adapter requirements

A new course tutor should have a small local adapter/context that maps the course
repository to this shared contract.

At minimum, define:

- exact compatible workspace-control checkpoint/version;
- root routing entry point;
- course/instructor authority;
- assignment ingestion route;
- source-evidence and semantic-synthesis owners;
- tutoring protocol entry;
- mastery snapshot/log paths;
- skill/dependency path;
- assessment-scope/relevance owner when applicable;
- per-assignment learning path;
- communications-ingestion owner when applicable;
- report/code/document-artifact owners;
- notation owner;
- local runtime/environment;
- allowed automatic mutation scope;
- default tutoring mode;
- artifact validation rules, including whether any visual/human gate is truly
  required.

The local adapter should point to this shared contract rather than copy it
verbatim.

## Default mutation recommendation for course tutors

A practical default for managed private course repositories is:

### Tutor may update directly

- problem learning records;
- mastery snapshot/log;
- skill map when a genuinely new durable dependency is established;
- assignment status/indexes;
- report source;
- assignment code/results/records;
- reproducibility metadata.

### Tutor should obtain or respect a project-defined gate for

- destructive history changes;
- deleting source/evidence;
- changing instructor authority/source;
- submitting to external systems;
- sending messages/emails;
- irreversible external actions;
- ambiguous high-impact choices.

Git history and bounded mutation scope provide rollback for ordinary tracked
coursework edits.

## Evaluation framework

Evaluate tutors on separate dimensions.

### Routing

- starts from the correct entry point;
- reads only needed owners/sources;
- reroutes on task transitions.

### Pedagogy

- diagnoses atomically;
- teaches minimally;
- returns control;
- requires evidence;
- separates completion from mastery.

### Persistence

- records evidence faithfully;
- avoids overpromotion;
- preserves misconceptions/traps;
- keeps snapshot/log/history roles distinct.

### Artifact production

- satisfies assignment contract;
- maintains provenance;
- produces reproducible code/results;
- builds clean reports;
- performs artifact QA.

### Operation

- uses authorized execution mode;
- protects repository state;
- validates diffs;
- commits/pushes safely;
- rereads durable state.

### Recovery

- can finish an assignment under deadline without falsifying mastery;
- can later recover into mastery mode and close gaps.

### Portability

- works with ChatGPT+human;
- works with connected direct tools;
- can hand off to Codex through durable state;
- does not require private conversation memory.

## Proven HW1 behaviors to preserve

The MTH 602 HW1 evaluation demonstrated several high-value behaviors that future
tutors should retain:

- unassessed was not treated as weak;
- assignment completion and mastery remained separate;
- a deadline-driven autonomous completion pass did not falsely promote P5 or
  coding concepts;
- the tutor later returned to mastery mode and required fresh behavioral
  evidence;
- direct repository updates substantially reduced friction;
- the tutor refused several promotions until transfer checks were passed;
- a later problem supplied legitimate transfer evidence for an
  `independent → exam-ready` promotion;
- per-problem local identity/provenance lists made the report easier to audit;
- reproducible coding work preserved seed, split, records, figures, and a
  reproduction command;
- final artifacts were visually reviewed;
- post-submission tutoring could improve mastery independently of the already
  finished artifact.

These are design requirements, not course-specific facts.

## Anti-patterns

Avoid:

- equating "submitted" with "mastered";
- marking tutor-generated solutions as student evidence;
- refusing to help finish urgent work merely because teaching is incomplete;
- silently completing urgent work while pretending it was learned;
- requiring Bash for every edit when a safe direct tool is available;
- allowing direct tools to bypass Git/evidence/validation;
- duplicating this whole contract into every course repository;
- treating one conversation's mode as permanent;
- giant up-front prerequisite exams;
- broad recursive repository ingestion;
- overwriting domain authority with control-plane policy.

## Acceptance tests for a new tutor

Before trusting a new course tutor, run cold-start tests that cover:

1. new problem with all relevant skills unassessed;
2. misconception requiring targeted remediation;
3. automatic learning/mastery persistence;
4. report/code artifact creation;
5. task transition into shared operator workflow;
6. direct-tool mutation;
7. human-terminal mutation;
8. deadline-driven COMPLETION mode;
9. later MASTERY_RECOVERY with fresh retests;
10. delayed EXAM_READINESS promotion;
11. mid-conversation rerouting;
12. executor handoff through workspace-control.

The goal is not identical wording across tutors.

The goal is consistent semantics, evidence, authority, and durable recoverability.
