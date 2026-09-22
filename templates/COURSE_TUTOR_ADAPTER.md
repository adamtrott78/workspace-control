# Course Tutor Adapter Template

Status: **template v0.1**

Use this as a small project-local adapter when creating a repository-backed
course tutor.

Do not copy the full shared operator or tutoring contracts into the course
repository.

Instead, map local course owners to the shared contracts.

## Shared contracts

This course tutor follows:

- `workspace-control/policies/TUTORING_CONTRACT.md`;
- `workspace-control/policies/OPERATOR_WORKFLOW.md`;
- `workspace-control/policies/PORTABILITY_CONTRACT.md` when executor handoff or
  cross-project portability matters.

The course repository remains authoritative for course-specific truth.

## Course identity

Fill in:

- course:
- term:
- instructor:
- student repository:
- instructor/upstream repository, if any:
- primary local checkout:
- primary runtime/environment:
- submission system:
- canonical branch:

## Root route

A fresh tutor starts from the course repository `README.md`.

The root README should route tasks such as:

| Task | Local owner |
|---|---|
| Learn/solve an assignment problem | tutoring protocol + assignment context |
| Record learning/mastery | learning record + mastery owners |
| Build report/submission | assignment/report owner |
| Implement/validate code | assignment code/result owner |
| Interpret instructor material | course/source authority |
| Study for exam | tutoring + mastery + course indexes |
| Operator/Git/runtime work | shared operator policy + local supplement |

When the task changes ownership mid-conversation, reroute before acting.

## Local semantic-owner map

Fill in paths for this course:

- course/instructor authority:
- assignment ingestion context:
- tutoring protocol adapter:
- current mastery snapshot:
- chronological mastery log:
- skill/dependency map:
- notation owner:
- course/topic index:
- homework/assignment index:
- per-assignment learning record:
- report owner:
- code owner:
- result/provenance owner:
- local operator supplement:

If a role does not yet exist, create it deliberately rather than silently using
chat memory as the owner.

## Default tutoring mode

Choose one:

- `LEARNING`
- another course-specific default that maps clearly to the shared contract.

Recommended default: `LEARNING`.

The tutor should switch naturally when the user's intent changes, including:

- deadline-driven `COMPLETION`;
- post-submission `MASTERY_RECOVERY`;
- later `EXAM_READINESS`.

## Mastery vocabulary

Recommended shared states:

- `unassessed`
- `blocked`
- `partial`
- `guided`
- `independent`
- `exam-ready`

If this course uses different labels, document the exact mapping here.

## Automatic mutation authority

Define what the tutor may update directly after the user has authorized use of
the repository.

Recommended default for a private managed course repository:

### Directly allowed

- assignment learning records;
- mastery snapshot;
- mastery log;
- problem/homework indexes;
- report source;
- assignment code;
- numerical/result records;
- reproducibility metadata;
- local skill map only when a genuinely durable dependency change is supported.

### Require an explicit project/user gate

- deleting authoritative instructor material;
- destructive Git/history changes;
- external submission;
- email/message sending;
- irreversible external actions;
- ambiguous high-impact choices.

All direct mutation still follows the shared operator workflow.

## Assignment completion versus mastery

Define local status wording so these are never conflated.

Recommended concepts:

- not started;
- learning in progress;
- tutoring complete / report pending;
- solution completed with guidance;
- report integrated / validated;
- submitted.

Tutor-generated work does not promote mastery.

## Problem provenance convention

For technical solutions, use a local section such as:

> Identities, definitions, and provenance used in this problem

Number locally:

`(I1), (I2), ...`

Restart numbering for each problem.

Record the source category for important facts:

- assignment-given;
- instructor/lecture;
- adopted textbook/reference;
- standard identity;
- explicit assumption.

Invoke those local identities in the solution where useful.

## Code/reproducibility contract

For coding assignments, define the minimum durable evidence:

- input identity:
- environment:
- seed:
- split/index identity:
- algorithm:
- source path:
- result record:
- figure/table generation:
- reproduction command:
- artifact validation:

The exact requirements remain course/assignment-specific.

## Report validation contract

Define:

- source path:
- build command:
- expected final artifact:
- freshness check:
- log/static checks:
- visual review requirements:
- submission packaging:
- whether final PDF/source is tracked:

Compilation success alone is not artifact validation.

## Cold-start read route

For each common task, document the smallest correct route from `README.md`.

A tutor should not need:

- prior chat memory;
- a prose handoff;
- recursive repository ingestion;
- another course repository's private context.

## Persistence boundary

At meaningful tutoring boundaries, persist:

- what was initially known;
- what was taught;
- misconceptions;
- independent evidence;
- unresolved retests;
- artifact completion status;
- whether tutor-generated work occurred.

Keep the current mastery snapshot concise.

## Evaluation

Before relying on this tutor for major coursework, run the shared procedure:

`workspace-control/procedures/TUTOR_EVALUATION.md`

Preserve the evaluation commit/branch and classify any defect as:

- routing;
- pedagogy;
- persistence;
- artifact;
- operation;
- portability;
- local course-content defect.

## Local exceptions

Document only genuine course-specific deviations from the shared contracts here.

Do not restate shared policy merely for convenience.
