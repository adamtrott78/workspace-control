<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/cis560-new-content-ingestion-hw2.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: cis560-new-content-ingestion-hw2
- Title: CIS560 new-content ingestion + HW2 bootstrap and assignment work
- Status: SUSPENDED
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

Obtain from the user the additional CIS560 course-content inputs covered since the 9c5e492354449186898b5f038e227e5a92d15005 checkpoint, including exact Sipser sections/references and any instructor notes/messages needed to establish coverage. Also obtain the authoritative HW2 PDF, but do not inspect/solve HW2 until the new course-content ingestion is complete. Resume with course_content_intake and preserve typed provenance.

## Remaining work

- Receive and ingest the additional instructor-covered course topics/material and exact Sipser sections since the current durable checkpoint.
- Inspect and ingest the full authoritative HW2 PDF only after course-content ingestion is current.
- Bootstrap homework/hw02 local owners, assignment contract, LEARNING state, source routing, and problem-to-skill/source mappings.
- Begin the first HW2 problem in LEARNING mode only after ingestion/bootstrap validation.
- Build and validate only the artifact types actually required by HW2.
- Synchronize final task state, establish HANDOFF_SAFE, and archive when complete.

## Blockers / gates

- Additional CIS560 course-content evidence since the 9c5e492354449186898b5f038e227e5a92d15005 durable checkpoint has not yet been provided in this task.
- The authoritative HW2 PDF has not yet been uploaded in this task.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/cis560-new-content-ingestion-hw2.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
