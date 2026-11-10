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

Validate the current PR #595 head, whose implementation checkpoint is c8eca3ddc7915b6bc5ce1e40bc0f8866c8d7be89 and whose following commit is derived state synchronization only. Do not run the live upgrade until that exact PR head passes the Workspace Shell/PADataset Python contract suite. Then run the upgrade from the exact validated head; it must clone PADataset execution source at 17e1147614f27702e43565089d618182ff71c5af and bind the untouched historical checkout read-only under /srv/workspace-shell/PADataset-evidence.

## Remaining work

- Run exact-head repository validation for the historical-evidence redesign and fix any regressions.
- Execute the live upgrade from the validated head; preserve the 107 GB historical checkout in place and expose it only by read-only bind mount.
- Reinstall/re-register the Workspace Shell plugin once so ChatGPT discovers the frozen PADataset/research-bounded tool schema.
- Run live positive and negative Workspace Shell acceptance for PADataset.
- Hand control back to the MTH602 Stage 00 provenance recovery task.
- Wire research-bounded to the real DNNs/CUDA runtime internally without changing the external MCP schema.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
