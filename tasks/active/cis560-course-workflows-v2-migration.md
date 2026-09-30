<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/cis560-course-workflows-v2-migration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: cis560-course-workflows-v2-migration
- Title: CIS560 Course Workflows v2 Migration
- Status: PLANNED
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
- Remote checkpoint: 1af3ce7022d079b89f0fbca32f313a6853db1c60
- Remote verified: True

## Next safe action

Start only from CIS560-AdamTrott README.md at 1af3ce7022d079b89f0fbca32f313a6853db1c60 on branch tutor-framework. Follow the repository's own durable routes; use experiments B/C only as evidence, not as new task state. Resolve the exact existing shared compatibility mechanism before mutation. If the branch moved from 1af3ce7022d079b89f0fbca32f313a6853db1c60, refresh this capsule first. Preserve course facts and do not reread external mail unless a migration regression genuinely requires it.

## Remaining work

- Recover CIS560 root/tutor/source/experiment owners.
- Map the promoted course adapter and communications-ingestion semantics.
- Adopt the promoted shared checkpoint explicitly if validated.
- Run cold-start/tutoring/communications-idempotency regressions.
- Checkpoint and verify the migrated project state.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/cis560-course-workflows-v2-migration.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
