<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/cis560-course-workflows-v2-migration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: cis560-course-workflows-v2-migration
- Title: CIS560 Course Workflows v2 Migration
- Status: IN_PROGRESS
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

On CIS560-AdamTrott tutor-framework at exact parent 1af3ce7022d079b89f0fbca32f313a6853db1c60, update only README.md, COURSE.md, and study/TUTORING.md to bind the promoted workspace-control checkpoint 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9, map the shared course/communications workflow roles, and replace the live conversational tutor-builder/tutor authority split with role-neutral semantic mutation boundaries. Preserve all course facts, mastery state, homework state, source records, experiment B/C evidence, and historical boundary-correction evidence. Then verify the exact changed scope before regression validation.

## Remaining work

- Update the existing CIS560 compatibility pins to workspace-control@0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9 and map promoted shared workflow roles without copying shared policy.
- Replace remaining live tutor-builder/tutor authority hierarchy with durable semantic-owner and mutation-boundary language while preserving the historical correction record.
- Run cold-start, tutoring/mastery, communications-ingestion/idempotency, artifact, and portability regressions.
- Checkpoint and independently verify the migrated CIS560 tutor-framework state.

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
