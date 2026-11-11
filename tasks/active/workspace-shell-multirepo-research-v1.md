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

Validate this exact state-only authority snapshot. Do not perform another live refresh until that validation passes.

## Remaining work

- Validate this state-only authority snapshot binding workspace-control ca2241d44d5563b137f4c6978b33dfc060d2a968 and PADataset 4c095352bfe128e93f794112741efdb7a66b9c38.
- After PASS, operator installs workspace-control execution ca2241d44d5563b137f4c6978b33dfc060d2a968 while preserving PADataset 4c095352bfe128e93f794112741efdb7a66b9c38.
- Verify live exact bindings and rerun tests/test_multisurrogate_dqnguard.py through research-bounded.
- Prepare one known-only four-class backbone target fold with 16,384 cache lineage and no target-informed checkpoint selection.
- Run Architecture C smoke/small-real evaluator and validate result_record.json.

## Blockers / gates

- Live Workspace Shell still uses execution 72073976f02ca151c6ee68128175c51b069be42c; validated BLAS runtime fix ca2241d44d5563b137f4c6978b33dfc060d2a968 is not installed yet.
- The next mutation is root-owned and must use the existing rollback-capable operator upgrade after this state-only authority snapshot passes validation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
