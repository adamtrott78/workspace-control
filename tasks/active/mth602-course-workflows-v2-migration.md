<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-course-workflows-v2-migration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-course-workflows-v2-migration
- Title: MTH602 Course Workflows v2 Migration
- Status: BLOCKED_RUNTIME
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

Obtain the exact small HW1 report runtime inputs without using the GitHub connector for large-file transfer (minimum: homework/hw01/report/main.tex and homework/hw01/input/hw1.csv, or a small archive containing them). From those exact inputs, run a clean LaTeX build, verify successful output, render the newly built PDF to page images, and visually inspect every page. If that regression passes, mark regression_validation VALIDATED, complete HANDOFF_SAFE, archive this migration task, and do not resume or mutate the separately suspended HW2 task.

## Remaining work

- Run a clean HW1 LaTeX compile from exact repository inputs in the available runtime.
- Render the newly built PDF to page images and visually inspect every page.
- Record the artifact regression result, establish final HANDOFF_SAFE, archive mth602-course-workflows-v2-migration, and leave mth602-new-unit-ingestion-hw2-prep suspended for coordinator refresh.

## Blockers / gates

- Fresh LaTeX build/render/visual-QA regression cannot run in the current runtime because no MTH602 checkout/artifact is mounted and the container cannot resolve github.com. Supply/materialize the exact small HW1 report inputs (at minimum homework/hw01/report/main.tex and homework/hw01/input/hw1.csv, or a small HW1 report/input zip) rather than transferring large binaries through the GitHub connector.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-course-workflows-v2-migration.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
