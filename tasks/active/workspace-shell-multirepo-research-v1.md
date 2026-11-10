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
- Remote checkpoint: 40b3dd8cddd87270bde107516022d4e4426c0671
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 17e1147614f27702e43565089d618182ff71c5af
- Remote verified: true

## Next safe action

Validate the current PR #595 head, whose implementation checkpoint is 40b3dd8cddd87270bde107516022d4e4426c0671 and whose following commits are state/handoff synchronization only. Do not execute the live upgrade operator until that exact PR head passes bounded repository validation. Then execute the operator on Lambda against PADataset expected SHA 17e1147614f27702e43565089d618182ff71c5af; fail closed on any mismatch.

## Remaining work

- Run exact-head repository validation and fix any regressions.
- Update the task checkpoint to the validated implementation head and synchronize derived handoff.
- Execute the live upgrade operator on Lambda only from the validated clean workspace-control head.
- Verify the historical PADataset checkout exact branch/head/status without mutating it; abort if the expected SHA binding is wrong.
- Run live positive and negative Workspace Shell acceptance for PADataset.
- Hand control back to the MTH602 Stage 00 provenance recovery task.

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
