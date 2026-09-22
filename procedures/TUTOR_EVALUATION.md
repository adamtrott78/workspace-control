# Repository-Backed Tutor Evaluation Procedure

Status: **provisional v0.1**

## Purpose

Evaluate a new or modified course tutor from a genuine cold start and determine
whether failures come from:

- routing;
- pedagogy;
- persistence;
- artifact production;
- operator behavior;
- executor portability;
- course-specific content.

This procedure is intentionally reusable across courses.

## Evaluation discipline

A cold-start test should pin:

- repository;
- branch lineage;
- exact commit;
- allowed sources;
- forbidden prior context;
- mutation restrictions for the phase being tested.

Do not rescue the tutor by naming files or rules it was supposed to discover.

When a test intentionally becomes non-blind, record that transition.

## Transcript-export caveat

Chat exports may omit user messages.

Do not classify "the tutor answered its own question" from an exported transcript
alone when surrounding context suggests a missing turn.

Prefer:

- the live conversation;
- screenshots;
- durable learning records;
- explicit user confirmation;
- repository evidence.

## Stage 1 — cold-start routing

Prompt a fresh tutor to perform one real course task.

Require it to start only at the root route.

Evaluate whether it independently finds:

- exact assignment/problem contract;
- tutoring owner;
- relevant course/instructor source;
- mastery snapshot;
- skill dependencies;
- per-assignment learning record;
- notation when relevant.

Expected behavior:

- no recursive repository inventory;
- no prior-chat assumptions;
- no inference that lecture exposure equals mastery;
- no inference that unassessed equals weak.

## Stage 2 — initial diagnosis

Use a problem with at least one unknown mastery state.

Evaluate whether the tutor:

- identifies the dependency chain;
- chooses the earliest useful diagnostic;
- asks one focused question rather than a giant quiz;
- does not reveal the whole assigned solution prematurely.

## Stage 3 — remediation loop

Introduce or naturally expose a misconception.

Evaluate whether the tutor:

- names the exact missing concept;
- teaches the smallest unit needed;
- immediately returns control;
- requires the student to use the concept;
- distinguishes arithmetic slips from conceptual errors;
- does not promote based on "I get it."

## Stage 4 — mastery evidence

Require fresh transfer.

Evaluate whether:

- `guided` and `independent` remain distinct;
- promotion is supported by actual student behavior;
- same-session reproduction is not automatically `exam-ready`;
- later failures can block or reverse promotion.

## Stage 5 — pedagogical persistence

Without naming exact files, ask the tutor to preserve what the interaction
established.

First test planning only.

The tutor should discover the local owners for:

- detailed learning history;
- current mastery snapshot;
- chronological mastery log.

It should identify files that should **not** change.

Then authorize mutation.

Evaluate:

- evidence fidelity;
- mastery conservatism;
- scope;
- Git diff;
- commit boundary;
- post-push reread.

## Stage 6 — report/artifact transition

Move from tutoring to producing the assignment artifact.

Do not explicitly name the operator file during a blind routing test.

Evaluate whether the tutor notices the task-owner transition and loads:

- report/code owner;
- shared operator workflow;
- local artifact validation rules.

This is a critical regression test for continuous routing.

## Stage 7 — execution-mode tests

### HUMAN_TERMINAL

Require a local/runtime operation.

Expected:

- bounded copy/paste block;
- child-shell safety;
- user returns exact evidence;
- no claim of execution before evidence.

### DIRECT_TOOL

Grant direct mutation authority.

Expected:

- direct edits/commits are allowed;
- mutation scope remains bounded;
- actual diff is validated;
- push/remote identity is verified;
- pushed state is reread.

Do not mark direct execution as a defect merely because no Bash block was used.

### HYBRID

Use a task requiring both direct repository tools and local runtime.

Expected:

- clear synchronization boundary;
- no assumption that remote mutation updated the local checkout;
- intentional reinspection before local mutation.

## Stage 8 — artifact validation

For a report/code assignment, verify that the tutor distinguishes:

- process exit;
- result correctness;
- artifact correctness;
- visual QA;
- final submission state.

For PDFs/slides/figures, include a visual review test.

For code, include deterministic/reproducible evidence where the assignment
supports it.

## Stage 9 — deadline completion

Create or wait for a real scenario in which the student explicitly requests
completion before mastery.

Evaluate whether the tutor:

- switches to `COMPLETION` mode;
- finishes the required artifact competently;
- may directly implement code/report work when authorized;
- records the unfinished learning honestly;
- does not promote tutor-generated work to student mastery;
- leaves actionable recovery targets.

A tutor should not fail this stage merely because it helps finish the assignment.

The key requirement is the completion/mastery firewall.

## Stage 10 — mastery recovery

After submission, ask to actually learn the concepts that were completed under
deadline.

Evaluate whether the tutor:

- starts from durable mastery state;
- prioritizes unfinished dependencies;
- treats the completed solution as study context, not proof;
- asks the student to perform work;
- uses fresh examples;
- promotes only after independent transfer.

This is one of the most important tests of the architecture.

## Stage 11 — exam readiness

At a later time or meaningfully different context, test retained skills cold.

Evaluate whether:

- scaffolding is minimized;
- the tutor can demote on failure;
- `exam-ready` requires later/transfer evidence;
- not every independent skill is mechanically promoted.

## Stage 12 — provenance quality

Inspect a finished technical solution.

Prefer per-problem local lists such as:

> Identities, definitions, and provenance used in this problem

Evaluate whether:

- labels restart locally;
- assignment/instructor/standard facts are distinguishable;
- solution steps invoke the relevant identities;
- unstated assumptions are not hidden behind labels;
- report remains readable rather than citation-heavy.

## Stage 13 — coding/reproducibility

For a coding assignment, evaluate durable provenance:

- input identity/hash;
- source path;
- seed;
- split/index identity;
- algorithm/solver;
- numerical records;
- figures/tables;
- reproduction command;
- uncertainty/inference where relevant.

Then separately evaluate whether the student actually understands those concepts.

## Stage 14 — executor handoff

Checkpoint the task through workspace-control and switch executor.

Run both directions when possible:

```text
Codex → ChatGPT/direct-tool or ChatGPT+human
ChatGPT/direct-tool or ChatGPT+human → Codex
```

The receiving executor should need only:

- workspace-control entry route;
- durable task capsule;
- owning project context/evidence.

A special prose handoff should not be required for a mature portable workflow.

## Evaluation output

For each stage, record:

- `PASS`;
- `PASS_WITH_NOTE`;
- `FAIL`;
- `NOT_TESTED`.

For every failure, classify the primary defect:

- `ROUTING_DEFECT`;
- `PEDAGOGY_DEFECT`;
- `PERSISTENCE_DEFECT`;
- `ARTIFACT_DEFECT`;
- `OPERATOR_DEFECT`;
- `PORTABILITY_DEFECT`;
- `COURSE_CONTENT_DEFECT`;
- `TOOLING_DEFECT`.

Also record severity:

- minor;
- major;
- blocking.

## Regression criteria

A tutor architecture change should not be accepted merely because it fixes the
specific failing prompt.

Retest at least:

- cold startup;
- mid-conversation rerouting;
- learning persistence;
- direct mutation;
- deadline completion;
- post-submission recovery;
- artifact validation.

Avoid problem-specific patches when a general routing or ownership defect is the
real cause.

## Baseline established by MTH 602 HW1

The MTH 602 HW1 evaluation provides a useful behavioral baseline:

- strong cold-start routing;
- targeted prerequisite remediation;
- conservative mastery persistence;
- later transfer-based promotion;
- deadline-driven autonomous completion with honest mastery state;
- reproducible code/report production;
- local per-problem identity/provenance lists;
- post-submission mastery recovery;
- direct GitHub operation that was efficient and successful.

Future tutor implementations should aim to preserve those strengths while
improving shared routing and cross-executor portability.
