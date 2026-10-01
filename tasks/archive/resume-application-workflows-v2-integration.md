<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/archive/resume-application-workflows-v2-integration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: resume-application-workflows-v2-integration
- Title: Resume/Application Workflows v2 Integration
- Status: COMPLETE
- Capsule schema: v2

## Goal

Evaluate and explicitly integrate the promoted reusable document-artifact mechanics with the existing PADataset resume/application domain, including a justified decision on whether that private domain should remain in PADataset or migrate to a dedicated repository; do not move it automatically.

## Workflow

- Repository: workspace-control
- Path: workflows/document-artifact-build.v1.json
- Checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9

## Repositories

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9
- Remote verified: True

### PADataset

- Intent: mutate
- Remote branch: resume-framework
- Remote checkpoint: 405e99b67df34caadc690722b210b49b233fc45c
- Remote verified: True

## Next safe action

Task complete. Use tasks/archive/resume-application-workflows-v2-integration.json only for audit or as evidence for a separately authorized future career/application repository migration; no further action is required by this task.

## Remaining work

- None.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/archive/resume-application-workflows-v2-integration.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
