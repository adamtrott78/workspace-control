<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/cis560-new-content-ingestion-hw2.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: cis560-new-content-ingestion-hw2
- Title: CIS560 new-content ingestion + HW2 bootstrap and assignment work
- Status: IN_PROGRESS
- Capsule schema: v2

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
- Remote checkpoint: e6ee68912a63eb2373780fd9b5ec3bcc42738084
- Remote verified: true

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9
- Remote verified: true

## Next safe action

Begin Homework 2 Problem 2-1 in LEARNING mode. Present the exact Sipser 1.36 task context without giving the construction away, then ask the smallest diagnostic: what finite information would a machine need to remember while reading a unary string a^k in order to decide whether k is a multiple of n? Persist the student's response in homework/hw02/LEARNING.md before advancing.

## Remaining work

- Tutor and complete HW2 one bounded problem/subproblem at a time, beginning with Problem 2-1 in LEARNING mode.
- Persist actual student behavioral evidence and update mastery only when justified independently.
- Use the solution manual only after meaningful attempts and semantic prompt matching.
- Build and validate the required word-processed submission artifact after/alongside completed problem work without conflating artifact correctness with mastery.
- Leave Canvas submission to the user unless separately and explicitly authorized.
- Synchronize final task state, establish HANDOFF_SAFE, and archive when complete.

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
