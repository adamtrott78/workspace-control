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
- Remote checkpoint: 72073976f02ca151c6ee68128175c51b069be42c
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 4c095352bfe128e93f794112741efdb7a66b9c38
- Remote verified: true

## Next safe action

Operator-only root gate: run the validated multirepo upgrade from exact authority 2ea84019e40de2a3d2a8fa46427af6b4ff7fe3da with workspace-control execution 72073976f02ca151c6ee68128175c51b069be42c and PADataset 4c095352bfe128e93f794112741efdb7a66b9c38. Connected Workspace Shell cannot perform this mutation because privileged helper trust is intentionally empty/fail-closed.

## Remaining work

- Operator runs the validated rollback-capable multirepo upgrade from authority 2ea84019e40de2a3d2a8fa46427af6b4ff7fe3da, installing workspace-control execution 72073976f02ca151c6ee68128175c51b069be42c while preserving PADataset 4c095352bfe128e93f794112741efdb7a66b9c38.
- After PASS, verify both live exact bindings through ChatGPT Workspace Shell.
- Run tests/test_multisurrogate_dqnguard.py through research-bounded.
- Prepare the known-only four-class backbone target fold and run Architecture C smoke/small-real evaluation.

## Blockers / gates

- The remaining action is root-owned Workspace Shell runtime mutation. This task explicitly keeps privileged helper trust stores empty/fail-closed, and the connected Workspace Shell frontend cannot mint the required signed root approval.
- Live runtime still uses workspace-control execution 6466ff118127af1dfcc2dbf6aa69833fe1d06c04 until the operator runs the validated upgrade from authority 2ea84019e40de2a3d2a8fa46427af6b4ff7fe3da to execution 72073976f02ca151c6ee68128175c51b069be42c.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
