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
- Remote checkpoint: ce19452c644599bda23f6e3766c9390fa0d906db
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 17e1147614f27702e43565089d618182ff71c5af
- Remote verified: true

## Next safe action

Validate the current PR head after this authority-state normalization. If the Workspace Shell/PADataset repository suite passes, freeze that head as the independent authority snapshot and deploy execution candidate ce19452c644599bda23f6e3766c9390fa0d906db with PADataset 17e1147614f27702e43565089d618182ff71c5af using the corrected rollback-capable upgrade operator. Then re-test both durable task IDs before any PADataset Stage 00 read.

## Remaining work

- Validate the authority-state head that binds workspace-control execution candidate ce19452c644599bda23f6e3766c9390fa0d906db.
- Deploy the corrected multirepo upgrade with separate authority and execution snapshots; do not bypass the live task gate.
- Verify live visibility for workspace-shell-multirepo-research-v1 and mth602-final-multisurrogate-dqnguard-v1, then run positive/negative PADataset acceptance.
- Begin MTH602 Stage 00 provenance recovery from clean PADataset execution SHA 17e1147614f27702e43565089d618182ff71c5af plus the untouched historical evidence checkout.
- Wire research-bounded to the real DNNs/CUDA runtime internally without changing the external MCP schema.

## Blockers / gates

- The refreshed Workspace Shell schema and transport are healthy, but the live trusted authority snapshot is stale: both new task IDs return TASK_NOT_FOUND. No PADataset execution is permitted until the independent authority snapshot is refreshed and both task IDs pass the live gate.
- Exact-head repository validation must be rerun after normalizing the task-capsule result fields and binding workspace-control execution to candidate ce19452c644599bda23f6e3766c9390fa0d906db.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
