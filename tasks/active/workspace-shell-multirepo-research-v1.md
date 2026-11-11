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
- Remote checkpoint: ca2241d44d5563b137f4c6978b33dfc060d2a968
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 4c095352bfe128e93f794112741efdb7a66b9c38
- Remote verified: true

## Next safe action

Operator-only root gate: run the validated multirepo upgrade from exact authority 1a0df02b1199a9ca02702275df73c3d1da97a271, with workspace-control execution ca2241d44d5563b137f4c6978b33dfc060d2a968 and PADataset 4c095352bfe128e93f794112741efdb7a66b9c38. Connected Workspace Shell cannot perform this root-owned mutation because privileged helper trust is intentionally empty/fail-closed.

## Remaining work

- Operator runs validated rollback-capable upgrade from authority 1a0df02b1199a9ca02702275df73c3d1da97a271, installing workspace-control execution ca2241d44d5563b137f4c6978b33dfc060d2a968 and preserving PADataset 4c095352bfe128e93f794112741efdb7a66b9c38.
- Verify live exact workspace-control and PADataset bindings through ChatGPT Workspace Shell.
- Rerun tests/test_multisurrogate_dqnguard.py through research-bounded.
- Prepare one known-only four-class backbone target fold with cache_len=16384 and no target-informed checkpoint selection.
- Run Architecture C smoke/small-real evaluator and validate result_record.json.

## Blockers / gates

- Remaining action is root-owned Workspace Shell mutation. Privileged helper trust remains intentionally empty/fail-closed, so connected Workspace Shell cannot execute the refresh.
- Live runtime remains on workspace-control execution 72073976f02ca151c6ee68128175c51b069be42c until operator installs validated execution ca2241d44d5563b137f4c6978b33dfc060d2a968.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
