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
- Remote branch: workspace-shell-multirepo-v3-reconcile-20261111
- Remote checkpoint: 6466ff118127af1dfcc2dbf6aa69833fe1d06c04
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 4c095352bfe128e93f794112741efdb7a66b9c38
- Remote verified: true

## Next safe action

Run the validated rollback-capable Workspace Shell multirepo upgrade from exact authority head 3fb385039108074bef7b5d142bb4fc4781a5c9ab, with workspace-control execution 6466ff118127af1dfcc2dbf6aa69833fe1d06c04 and PADataset execution 4c095352bfe128e93f794112741efdb7a66b9c38. Require LOCAL_TASK_AUTHORITY=PASS and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS before Stage 03.

## Remaining work

- Operator executes hardened multirepo upgrade from authority head 3fb385039108074bef7b5d142bb4fc4781a5c9ab with workspace-control 6466ff118127af1dfcc2dbf6aa69833fe1d06c04 and PADataset 4c095352bfe128e93f794112741efdb7a66b9c38.
- Verify live Workspace Shell task visibility plus exact workspace-control and PADataset source bindings.
- Resume MTH602 Stage 03 deterministic tests and architecture-C smoke.

## Blockers / gates

- Live Workspace Shell runtime has not yet been refreshed to authority 3fb385039108074bef7b5d142bb4fc4781a5c9ab, workspace-control 6466ff118127af1dfcc2dbf6aa69833fe1d06c04, and PADataset 4c095352bfe128e93f794112741efdb7a66b9c38.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
