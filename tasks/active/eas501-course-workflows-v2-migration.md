<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/eas501-course-workflows-v2-migration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: eas501-course-workflows-v2-migration
- Title: EAS501 Course Workflows v2 Migration
- Status: PLANNED
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

Start only from EAS501-AdamTrott README.md at bccb636f35bbb0f530c8fa15b1a7b3d573193e07 on branch eas501-tutor-bootstrap. Read its workspace-control.lock.json and resolve the currently pinned shared contracts before touching any file. Compare those local semantics to the promoted course-bootstrap workflow pinned by this capsule; preserve the completed Exam 1 post-exam evidence, current Exam 2 planning/source material, and all existing mastery/assessment content. The branch baseline has already been deliberately refreshed after Exam 1, so do not reset or rebase it to the older 52eb8e44 checkpoint.

## Remaining work

- Recover EAS501 root routes and current workspace-control lock semantics.
- Map current tutor/assessment/source/mastery owners to the promoted adapter roles.
- Perform an explicit compatible_commit transition only after validation.
- Run cold-start/tutoring/assessment-relevance regressions.
- Checkpoint and verify the migrated project state.

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
