<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-course-workflows-v2-migration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-course-workflows-v2-migration
- Title: MTH602 Course Workflows v2 Migration
- Status: CHECKPOINTED
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

Run the final topology-aware HANDOFF_SAFE assessment for this synchronized checkpointed capsule. If it is HANDOFF_SAFE, mark completion VALIDATED, set the task COMPLETE with no remaining work/blockers, regenerate the derived Markdown immediately, archive the completed capsule/handoff, and leave the separately suspended mth602-new-unit-ingestion-hw2-prep task untouched.

## Remaining work

- Run the final topology-aware HANDOFF_SAFE assessment against this synchronized checkpointed capsule, then archive this migration task while leaving mth602-new-unit-ingestion-hw2-prep suspended for coordinator refresh.

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
