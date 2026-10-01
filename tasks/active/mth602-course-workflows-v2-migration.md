<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-course-workflows-v2-migration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-course-workflows-v2-migration
- Title: MTH602 Course Workflows v2 Migration
- Status: PLANNED
- Capsule schema: v2

## Goal

Explicitly migrate the current MTH602 repository integration to the promoted reusable course-workflow architecture while preserving its proven direct-visual source ingestion, tutoring/mastery state, homework/LaTeX report mechanics, and project-local authority.

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

### MTH602-AdamTrott

- Intent: mutate
- Remote branch: unit-ingestion-hw2
- Remote checkpoint: 20dc641dcb9b505efe53daa52932521d0927ef3a
- Remote verified: true

## Next safe action

Start only from MTH602-AdamTrott README.md at 20dc641dcb9b505efe53daa52932521d0927ef3a on branch unit-ingestion-hw2, then follow its documented routes. Read workspace-control course-bootstrap workflow at 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9 only through the exact binding in this capsule. Recover the existing source/tutoring/homework/report owners and current compatibility mechanism before mutation. Preserve the newly ingested lecture state and initialized HW2 contract/learning/provenance state exactly. Do not perform any HW2 problem-solving or mastery work as part of the migration.

## Remaining work

- Recover current MTH602 owners and compatibility state from the root route.
- Map missing shared adapter roles without duplicating shared policy.
- Adopt the promoted checkpoint explicitly if validation supports it.
- Run cold-start/source-ingestion/tutoring/LaTeX artifact regressions.
- Checkpoint and verify the migrated project state.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-course-workflows-v2-migration.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
