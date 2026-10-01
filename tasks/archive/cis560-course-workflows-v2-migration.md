<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/archive/cis560-course-workflows-v2-migration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: cis560-course-workflows-v2-migration
- Title: CIS560 Course Workflows v2 Migration
- Status: COMPLETE
- Capsule schema: v2

## Goal

Explicitly migrate the CIS560 tutor-framework integration to the promoted reusable course-workflow architecture while preserving course authority, durable tutoring state, and the proven communications-ingestion/idempotent parent-return behavior.

## Workflow

- Repository: workspace-control
- Path: workflows/course-bootstrap-migration.v1.json
- Checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9

## Repositories

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9
- Remote verified: True

### CIS560-AdamTrott

- Intent: mutate
- Remote branch: tutor-framework
- Remote checkpoint: 9c5e492354449186898b5f038e227e5a92d15005
- Remote verified: True

## Next safe action

Migration is complete and archived-ready. Future CIS560 work should start from CIS560-AdamTrott tutor-framework@9c5e492354449186898b5f038e227e5a92d15005 with the exact workspace-control compatibility/workflow checkpoint 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9; create a new durable task for any further mutation.

## Remaining work

- None.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/archive/cis560-course-workflows-v2-migration.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
