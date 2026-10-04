<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/cis560-new-content-ingestion-hw2.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: undefined
- Title: CIS560 new-content ingestion + HW2 bootstrap and assignment work
- Status: IN_PROGRESS
- Capsule schema: 2

## Goal

Bring CIS 560 durable course state current with all genuinely new instructor-covered topics and exact Sipser sections since the last checkpoint, ingest the authoritative Homework 2 PDF, bootstrap assignment-local HW2 routing and learning state, then tutor HW2 problem-by-problem and build/validate only the artifacts the assignment actually requires.

## Workflow

- Repository: workspace-control
- Path: workflows/course-assignment-work.v1.json
- Checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9

## Repositories

### CIS560-AdamTrott

- Intent: mutate
- Remote branch: tutor-framework
- Remote checkpoint: 9156e4e269d4ad10e5876b983ffb44864e1762e9
- Remote verified: true

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9
- Remote verified: true

## Current stage

- HW2 tutoring: VALIDATED
- Word-processed artifact build: VALIDATED
- Final validation / handoff: IN_PROGRESS pending user review and Canvas submission

## Artifact state

- Durable source: `homework/hw02/artifacts/SUBMISSION.md`
- Final PDF: `CIS560_HW2_Adam_Trott.pdf`
- Word source: cleaned DOCX with redundant Homework assignment labels removed
- Reusable format authority: `homework/REPORT_STYLE.md`
- Style parity: PASS against Problem Set 1 precedent
- Semantic validation: PASS
- Visual validation: PASS (8 pages inspected)
- Canvas submission: NOT_PERFORMED

## Next safe action

Present the final cleaned CIS560_HW2_Adam_Trott.pdf to the user for review. If no edits are requested, the next action is the user-owned Canvas submission; after confirmation, finalize HANDOFF_SAFE/archive.

## Remaining work

- User reviews the attached submission-ready DOCX and requests any desired wording/layout edits.
- User submits the final document to Canvas; external submission remains user-owned unless separately authorized.
- After submission confirmation or explicit closure, synchronize final HANDOFF_SAFE state and archive the task capsule.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/cis560-new-content-ingestion-hw2.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
