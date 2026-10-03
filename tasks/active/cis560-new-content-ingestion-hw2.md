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
- Remote checkpoint: edf5dc31df48abb785ed6b5635a0399bb2d784db
- Remote verified: true

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9
- Remote verified: true

## Next safe action

Inspect the full authoritative HW2 artifact and exact referenced Sipser items, then bootstrap homework/hw02 assignment-local owners and mappings without beginning solution work. Preserve the PDF as assignment authority and keep artifact requirements separate from mastery.

## Remaining work

- Receive and fully inspect the authoritative HW2 PDF.
- Bootstrap homework/hw02 local owners, exact assignment contract, LEARNING state, source routing, and problem-to-skill/source mappings.
- Resolve exact Sipser problem wording for any textbook-referenced HW2 items before tutoring them.
- Begin the first HW2 problem in LEARNING mode only after HW2 ingestion/bootstrap validation.
- Build and validate only the artifact types actually required by HW2.
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
