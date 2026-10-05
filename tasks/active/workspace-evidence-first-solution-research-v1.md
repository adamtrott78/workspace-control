<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-evidence-first-solution-research-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-evidence-first-solution-research-v1
- Title: Workspace Evidence-First Solution Research v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Promote a reusable workspace-level research-before-implementation workflow that lets any project/chat investigate comparable problems, current literature, open-source implementations, practitioner patterns, and candidate architectures before committing to a material implementation direction.

## Parent execution owner

research-engine-local-extract-redesign-v1

## Current stage

workflow_design_and_promotion

## Next safe action

Create an isolated workspace-control branch from main@aa24d3f25a54745bcffb607f9ff43310181c9b85 and implement the evidence-first solution-research procedure, workflow descriptor, and root-route discoverability. Validate with the workflow descriptor validator and workspace-control FULL_INTEGRATION tier before merging. Do not modify project-specific research-engine truth in this workspace-level task.

## Remaining work

- Write the workspace-level evidence-first research procedure.
- Write the reusable workflow descriptor.
- Add root-route discoverability without making research mandatory for trivial work.
- Run workflow validation, full workspace-control tests, and task contract regression.
- Merge the validated workflow and return its exact identity to the originating EXTRACT task.

## Blockers / gates

- None recorded.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-evidence-first-solution-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git state, and referenced owner evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
