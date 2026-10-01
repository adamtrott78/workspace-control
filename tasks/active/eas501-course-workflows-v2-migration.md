<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/eas501-course-workflows-v2-migration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: eas501-course-workflows-v2-migration
- Title: EAS501 Course Workflows v2 Migration
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Explicitly migrate EAS501 from its current pinned workspace-control compatibility contract to the promoted reusable course-workflow architecture while preserving current assessment/course state and project-local authority.

## Workflow

- Repository: workspace-control
- Path: workflows/course-bootstrap-migration.v1.json
- Checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9

## Repositories

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9
- Remote verified: true

### EAS501-AdamTrott

- Intent: mutate
- Remote branch: eas501-tutor-bootstrap
- Remote checkpoint: bccb636f35bbb0f530c8fa15b1a7b3d573193e07
- Remote verified: true

## Next safe action

On EAS501-AdamTrott:eas501-tutor-bootstrap, mutate only the existing adapter/routing layer from parent bccb636f35bbb0f530c8fa15b1a7b3d573193e07: advance workspace-control.lock.json compatible_commit from 450eebeef6b76a674913949863082277b6bdb811 to 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9; update COURSE_TUTOR.md and README.md to route the promoted content-ingestion, assessment-preparation, study-session, assignment/take-home-project, cheat-sheet, communications-ingestion, and document-artifact workflows to existing or deliberately future-created local owners. Preserve all practice/exam01, practice/exam02, course/source, mastery, skill-map, notation, and learning-record blobs unchanged. Then verify the exact changed-path set and remote checkpoint before regression validation.

## Remaining work

- Advance the existing workspace-control.lock.json compatibility pin explicitly to 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9 and map promoted reusable course workflow roles through the existing EAS501 adapters.
- Run cold-start, tutoring/mastery, assessment-relevance, source-routing, artifact/workflow, and executor-portability regressions while verifying authoritative evidence blobs remain unchanged.
- Checkpoint and independently verify the migrated EAS501 project state, establish final HANDOFF_SAFE state, and archive the migration task.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/eas501-course-workflows-v2-migration.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
