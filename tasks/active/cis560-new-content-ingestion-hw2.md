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
- Remote checkpoint: 9c5e492354449186898b5f038e227e5a92d15005
- Remote verified: true

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9
- Remote verified: true

## Next safe action

Ingest the newly provided Lecture 7–9 instructor material into CIS560 tutor-framework, treating Lecture 6 uploads as overlap/no-op, recording exact covered/read-next Sipser relationships without promoting mastery, then validate the resulting course/source/skill/notation state. Do not inspect or solve HW2 until this ingestion is complete.

## Remaining work

- Ingest the genuinely new Lecture 7–9 coverage and exact current Sipser section relationship, preserving the distinction between covered material, assigned reading, and next-topic guidance.
- Inspect and ingest the full authoritative HW2 PDF only after course-content ingestion is current.
- Bootstrap homework/hw02 local owners, assignment contract, LEARNING state, source routing, and problem-to-skill/source mappings.
- Begin the first HW2 problem in LEARNING mode only after ingestion/bootstrap validation.
- Build and validate only the artifact types actually required by HW2.
- Synchronize final task state, establish HANDOFF_SAFE, and archive when complete.

## Blockers / gates

- The authoritative HW2 PDF has not yet been uploaded in this task.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/cis560-new-content-ingestion-hw2.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
