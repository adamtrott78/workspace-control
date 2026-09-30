<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/resume-application-workflows-v2-integration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: resume-application-workflows-v2-integration
- Title: Resume/Application Workflows v2 Integration
- Status: PLANNED
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
- Remote checkpoint: 078461795be3c1d3e5c3845c81607166fac9fad3
- Remote verified: True

## Next safe action

Start only from PADataset README.md at 078461795be3c1d3e5c3845c81607166fac9fad3 on branch resume-framework, then follow the documented resume/application route to the smallest required owning contexts. Compare the existing resume production lifecycle to workspace-control document-artifact-build at 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9. First decide, from repository evidence, whether the domain should remain in PADataset or warrants a separate private repository; do not move or create a repository automatically. If the target branch moved from 078461795be3c1d3e5c3845c81607166fac9fad3, refresh this capsule before mutation.

## Remaining work

- Recover the PADataset resume/application route and existing builder/QA owners.
- Evaluate whether domain separation from PADataset is justified and record the decision.
- Integrate the promoted document-artifact mechanics without changing candidate truth.
- Run cold-start/build/render/semantic+visual-QA/bounded-revision regressions.
- Checkpoint and verify the resulting integration state.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/resume-application-workflows-v2-integration.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
