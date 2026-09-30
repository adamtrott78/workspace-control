<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/padataset-control-plane-v2-integration.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: padataset-control-plane-v2-integration
- Title: PADataset workspace-control v2 integration
- Status: SUSPENDED
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

## Next safe action

Use a separate fresh ChatGPT or Codex session for a read-only validation. Give it only repository adamtrott78/PADataset, branch lineage control-plane-v2-integration, pinned commit d6f6a7281f20d250423abd35ee5991841677e27d, and instruct it to start only from README.md with no prior handoff. Ask it to recover (1) the shared workspace-control/operator route, (2) PADataset versus workspace-control authority boundaries, (3) how an exact task-capsule workflow/checkpoint must be honored, and (4) what it would read next for a mutation/runtime task. It must not modify anything. Return that exact validation result to this task before project_regression.

## Remaining work

- Run the independent README-first ChatGPT/Codex cold-start validation against PADataset@d6f6a7281f20d250423abd35ee5991841677e27d.
- After that passes, perform project_regression by reviewing the exact integration diff and confirming the shared route preserves PADataset authority/task routing.
- Checkpoint final HANDOFF_SAFE state and archive the completed task.

## Blockers / gates

- Independent fresh-reader validation is required before project_regression; the implementation session must not self-certify that gate.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-control-plane-v2-integration.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
