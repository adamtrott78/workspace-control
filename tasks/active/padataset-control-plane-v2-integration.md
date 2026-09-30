<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/padataset-control-plane-v2-integration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: padataset-control-plane-v2-integration
- Title: PADataset workspace-control v2 integration
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Adopt the promoted workspace-control v2 operating model in PADataset with the smallest project-local integration necessary for durable cold starts, direct-tool-first execution, executor handoff, and task-state recovery while preserving PADataset-owned scientific/domain authority and existing research workflows.

## Workflow

- Repository: workspace-control
- Path: policies/OPERATOR_WORKFLOW.md
- Checkpoint: 03a51fdbe2a9153f2b5e45054eec6e927a9dda36

## Repositories

### PADataset

- Intent: mutate
- Remote branch: control-plane-v2-integration
- Remote checkpoint: d6f6a7281f20d250423abd35ee5991841677e27d
- Remote verified: true

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 03a51fdbe2a9153f2b5e45054eec6e927a9dda36
- Remote verified: true

## Next safe action

Re-review PADataset base 232d5fd506ac8bffa55c39591c9cf1198257e51f against integration head d6f6a7281f20d250423abd35ee5991841677e27d. Verify the changed-path set is exactly README.md and AGENTS.md, removing the inserted README operator section reconstructs the base README byte-for-byte, AGENTS.md contains routing only, and the pinned workspace-control workflow recovery entry satisfies v2 handoff binding. If all pass, complete and archive the task.

## Remaining work

- Perform project_regression by rechecking the exact base-to-head diff, verifying the original PADataset README/task router is preserved apart from the bounded operator-route insertion, and confirming AGENTS.md remains a thin adapter.
- Establish final v2 HANDOFF_SAFE state under the pinned workspace-control checker semantics.
- Archive the completed task after final JSON/Markdown synchronization.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-control-plane-v2-integration.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
