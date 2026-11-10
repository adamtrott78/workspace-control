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
- Remote checkpoint: 50395aad06ab719b8207d9e7d3d8270a6bb35030
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 4c095352bfe128e93f794112741efdb7a66b9c38
- Remote verified: true

## Next safe action

Wait only for exact-head candidate-scope validation of workspace-control 50395aad06ab719b8207d9e7d3d8270a6bb35030. Once validated, deploy the authority state produced by this task checkpoint with workspace-control exec 50395aad06ab719b8207d9e7d3d8270a6bb35030 and PADataset exec 4c095352bfe128e93f794112741efdb7a66b9c38; then verify both live task gates before Stage 03 execution.

## Remaining work

- Obtain exact-head candidate-scope validation for workspace-control 50395aad06ab719b8207d9e7d3d8270a6bb35030.
- Refresh the independent trusted authority and clean PADataset runtime snapshot to 4c095352bfe128e93f794112741efdb7a66b9c38 using the hardened upgrader.
- Run deterministic Stage 03 tests through research-bounded on the exact clean snapshot.
- Prepare one known-only four-class backbone target fold and run the reviewed architecture C small-real evaluation.

## Blockers / gates

- Workspace Shell live PADataset snapshot remains at 17e1147614f27702e43565089d618182ff71c5af while Stage 03 candidate is 4c095352bfe128e93f794112741efdb7a66b9c38.
- Hardened workspace-control execution candidate 50395aad06ab719b8207d9e7d3d8270a6bb35030 is queued for exact-head Lambda validation; do not deploy it until candidate-scope validation evidence is available.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
