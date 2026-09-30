<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/padataset-control-plane-v2-integration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: padataset-control-plane-v2-integration
- Title: PADataset workspace-control v2 integration
- Status: PLANNED
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
- Remote checkpoint: 232d5fd506ac8bffa55c39591c9cf1198257e51f
- Remote verified: true

## Next safe action

In a fresh ChatGPT conversation with GitHub access, open workspace-control/tasks/active/padataset-control-plane-v2-integration.json from main, follow the pinned workspace-control v2 route, then read PADataset README.md at control-plane-v2-integration@232d5fd506ac8bffa55c39591c9cf1198257e51f. Complete baseline_recovery before proposing or making PADataset mutations.

## Remaining work

- Recover the PADataset baseline from README.md and inspect only the existing operator/routing surfaces needed to design the integration.
- Define the smallest PADataset-local route/adapter changes needed to adopt workspace-control v2 without duplicating generic semantics.
- Implement the bounded integration on control-plane-v2-integration.
- Run a fresh-reader ChatGPT/Codex cold-start validation from the PADataset root route.
- Review the exact integration diff and verify that scientific code/configuration/results/paper semantics did not change.
- Checkpoint the verified PADataset branch, establish final HANDOFF_SAFE state, and archive the completed task.

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
