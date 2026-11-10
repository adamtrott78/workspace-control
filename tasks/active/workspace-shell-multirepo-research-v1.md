<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-multirepo-research-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-multirepo-research-v1
- Title: Workspace Shell multi-repo PADataset research access v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Extend the live Workspace Shell v1 lineage with a first-class PADataset target that supports exact-SHA/task-bound Git provenance, bounded read-only evidence inspection, and sandboxed network-denied research execution without exposing a generic shell or making the historical PADataset checkout writable.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-multirepo-research-v1
- Remote checkpoint: c8eca3ddc7915b6bc5ce1e40bc0f8866c8d7be89
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 17e1147614f27702e43565089d618182ff71c5af
- Remote verified: true

## Next safe action

Start a fresh ChatGPT conversation with Workspace Shell connected. First inspect the model-visible Workspace Shell schema and confirm workspace_shell_exec target includes PADataset and profile includes file-list/file-read/file-hash/research-bounded. Then test live task visibility for workspace-shell-multirepo-research-v1 and mth602-final-multisurrogate-dqnguard-v1. If visible, begin Stage 00 read-only PADataset provenance recovery; if TASK_NOT_FOUND persists, diagnose the live frontend authority_root before any execution.

## Remaining work

- Fresh-chat remount of refreshed Workspace Shell tool schema.
- Verify new task-capsule visibility in the live authority root.
- Run live positive and negative Workspace Shell acceptance for PADataset.
- Begin MTH602 Stage 00 provenance recovery from clean execution SHA 17e1147614f27702e43565089d618182ff71c5af plus read-only historical evidence mount leaf2026-review-1571342865@b5a09cede6680b9e2a53eac244db4fbd7eaf76ec.
- Wire research-bounded to the real DNNs/CUDA runtime internally without changing the external MCP schema.

## Blockers / gates

- Current ChatGPT conversation retains the old mounted Workspace Shell function schema even after successful app tool refresh. Live app transport is healthy. Start a fresh ChatGPT conversation so Workspace Shell is remounted with the refreshed PADataset/research-bounded schema.
- After fresh-chat remount, verify the newer durable task capsules are visible through the live authority root before Stage 00. Old task workspace-shell-mcp-v1 is visible; newer task IDs returned TASK_NOT_FOUND in this stale-schema conversation and require recheck from the refreshed session.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
