<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/eas501-course-workflows-v2-migration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: eas501-course-workflows-v2-migration
- Title: EAS501 Course Workflows v2 Migration
- Status: VALIDATING
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
- Remote checkpoint: 0e5ac0d14bf5a68e7cb0f48f7e9b82b79e58a43d
- Remote verified: true

## Next safe action

From EAS501-AdamTrott:eas501-tutor-bootstrap@0e5ac0d14bf5a68e7cb0f48f7e9b82b79e58a43d, run read-only migration regressions: prove root cold-start routing through the exact lock and local adapter; verify tutoring/mastery semantics; verify Exam 2 contextual assessment relevance remains separate from current-course authority; verify source routing and Exam 1 artifact strategy remain intact; confirm all baseline course/practice/study evidence blobs are unchanged; and verify every mapped shared workflow exists at workspace-control@0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9. Do not perform live Exam 2 tutoring.

## Remaining work

- Run cold-start, tutoring/mastery, assessment-relevance, source-routing, artifact/workflow, and executor-portability regressions against the migrated checkpoint while confirming all authoritative evidence blobs remain unchanged.
- Reverify the final EAS501 branch and exact shared workflow identity, establish final HANDOFF_SAFE state, and archive the migration task.

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
