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

Wait for workspace-control PR #70 validation run 37369399893. If it passes, merge PR #70 without additional scope expansion, verify the canonical main commit and merged workflow contents, then checkpoint this task as COMPLETE/CHECKPOINTED-equivalent and return the exact workflow identity to `research-engine-local-extract-redesign-v1`. If CI fails, diagnose only the demonstrated validation defect.

## Remaining work

- Wait for full-integration validation of PR #70.
- If validation passes, merge PR #70 and verify canonical workspace-control main.
- Record the exact durable workflow identity for workflows/evidence-first-solution-research.v1.json.
- Return that identity to research-engine-local-extract-redesign-v1 so the originating task can formally bind the reusable workflow.

## Blockers / gates

- Workspace Control Validation run 37369399893 is queued for PR #70; no additional workflow mutation is justified unless validation fails.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-evidence-first-solution-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git state, and referenced owner evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
