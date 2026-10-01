<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/archive/mth602-course-workflows-v2-migration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-course-workflows-v2-migration
- Title: MTH602 Course Workflows v2 Migration
- Status: COMPLETE
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
- Remote checkpoint: 0ed5957af97e2de887ef181f26a9966413daf857
- Remote verified: true

## Next safe action

No further work belongs to this completed migration. Keep mth602-new-unit-ingestion-hw2-prep suspended until its coordinator deliberately refreshes that capsule to MTH602 unit-ingestion-hw2@0ed5957af97e2de887ef181f26a9966413daf857; only then may HW2 work resume.

## Remaining work

- None.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/archive/mth602-course-workflows-v2-migration.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
