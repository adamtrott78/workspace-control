<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-hw3-exam1-prep.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-hw3-exam1-prep
- Title: MTH 602 HW3 + Exam 1 preparation
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Use the limited pre- and post-MILCOM study windows to bring MTH 602 course state current, ingest and complete Homework 3, determine the October 19 exam scope from authoritative evidence, identify high-priority weaknesses and likely tested skills, build a realistic study plan, and develop the permitted exam cheat sheet without inventing scope or rules.

## Workflow

- Repository: workspace-control
- Path: workflows/course-assessment-preparation.v1.json
- Checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9

## Repositories

### MTH602-AdamTrott

- Intent: mutate
- Remote branch: hw3-exam1-prep
- Remote checkpoint: b297c524d505715fe93f9a266d7d45564cbbe47f
- Remote verified: true

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9
- Remote verified: true

## Time-critical constraints

- Current date: 2026-10-08.
- MTH 602 exam: Monday, 2026-10-19.
- MILCOM travel / unavailable study period: Sunday, 2026-10-11 through Thursday night, 2026-10-15.
- Primary available MTH602 study windows: 2026-10-08 through 2026-10-10 and 2026-10-16 through 2026-10-18.
- CIS 560 midterm: Thursday, 2026-10-22.
- HW3 due date, exact exam scope/format, and cheat-sheet rules remain unresolved until authoritative evidence is ingested.

## Next safe action

In the new chat, start from workspace-control and this task capsule, then read MTH602 README.md / COURSE_TUTOR.md only as routed. Ask the user to provide the new course materials and authoritative HW3 artifact if they are not already attached. Ingest those first. At the same time, recover any explicit exam date/scope/format/cheat-sheet guidance already present in the provided course material. Do not guess HW3 due date, exam scope, or cheat-sheet rules.

## Remaining work

- Ingest the new course materials the user provides, preserving provenance and updating course/topic/skill routing without promoting mastery.
- Ingest the authoritative HW3 artifact and resolve its due date, exact deliverables, submission rules, and problem/source mappings.
- Work HW3 efficiently under the tutoring protocol, using it as both assignment completion and exam-relevance evidence where justified.
- Collect explicit and contextual evidence for the October 19 exam scope, format, and likely problem forms; keep uncertain topics labeled uncertain.
- Map likely exam scope to current mastery, prerequisites, traps, and stale evidence.
- Build a time-budgeted study plan centered on October 8-10 and October 16-18.
- Resolve cheat-sheet rules and iteratively build the highest-value sheet content.
- Run targeted study/retrieval practice, update readiness evidence, and finalize cheat sheet before the exam.

## Blockers / gates

- None at task creation; missing HW3/new-course-material inputs become explicit intake gates only if not provided in the receiving chat.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/mth602-hw3-exam1-prep.json`

Start from the normal `workspace-control` root route.

Treat the authoritative task capsule, its synchronized Markdown handoff, exact durable Git state, and referenced MTH602 evidence as the complete handoff.

Do not rely on previous conversation state or another chat's prose summary.

Follow the capsule's exact `next_safe_action`.

Important immediate context:
- MTH602 working branch: `hw3-exam1-prep`
- branch baseline: `b297c524d505715fe93f9a266d7d45564cbbe47f`
- exam: Monday, October 19, 2026
- user cannot meaningfully study during MILCOM travel from Sunday, October 11 through Thursday night, October 15
- usable MTH602 study windows are therefore primarily October 8-10 and October 16-18
- CIS 560 midterm follows Thursday, October 22

The task priorities are:
1. ingest the new MTH602 course materials the user provides;
2. ingest the authoritative HW3 artifact and determine its actual due date/deliverables before solving;
3. work HW3 efficiently under the existing tutoring protocol;
4. reconstruct exam scope/likely tested skills from authoritative and contextual course evidence without guessing;
5. map that scope against current mastery and known gaps;
6. build a realistic study plan for the remaining windows;
7. determine the allowed cheat-sheet format and build high-value cheat-sheet content;
8. preserve completion, mastery, readiness, and artifact state separately.

Do not invent exam coverage, HW3 requirements, or cheat-sheet rules. Use source evidence and label uncertainty explicitly.
