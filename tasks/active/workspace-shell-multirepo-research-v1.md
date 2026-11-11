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

Execute the already-validated rollback-capable multirepo runtime refresh from the exact authority-state head of branch state-workspace-shell-multirepo-v3-ready-20261111, using workspace-control execution 6466ff118127af1dfcc2dbf6aa69833fe1d06c04 and PADataset execution 4c095352bfe128e93f794112741efdb7a66b9c38. Do not start PADataset Stage 03 until the upgrader reports LOCAL_TASK_AUTHORITY=PASS and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS and live ChatGPT Workspace Shell confirms both bindings.

## Remaining work

- Run the hardened Workspace Shell multirepo upgrade from this exact authority-state branch, with workspace-control execution 6466ff118127af1dfcc2dbf6aa69833fe1d06c04 and PADataset execution 4c095352bfe128e93f794112741efdb7a66b9c38.
- Verify both durable task IDs through live Workspace Shell runtime_inventory and exact git_head/status/tree after the upgrade.
- Run tests/test_multisurrogate_dqnguard.py through research-bounded on the exact clean PADataset snapshot.
- Prepare one known-only four-class backbone target fold with 16,384 cache lineage and no target-informed checkpoint selection.
- Run architecture C smoke/small-real evaluator and validate result_record.json against the Stage 02 schema.

## Blockers / gates

- Live Workspace Shell runtime is not yet rebound to workspace-control 6466ff118127af1dfcc2dbf6aa69833fe1d06c04 and PADataset 4c095352bfe128e93f794112741efdb7a66b9c38.
- Stage 03 execution remains prohibited until the hardened multirepo upgrade succeeds and ChatGPT Workspace Shell re-verifies both exact task bindings.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
