<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/padataset-control-plane-v2-integration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: padataset-control-plane-v2-integration
- Title: PADataset workspace-control v2 integration
- Status: COMPLETE
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

Task complete. For future PADataset work, start from PADataset README.md at the intended ref and create or resume a separate workspace-control task capsule when durable coordination is required.

## Remaining work

- None.

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
