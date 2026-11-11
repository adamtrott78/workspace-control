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

Wait for exact policy validation #442 / run 43075570444 / job 130714359098 on PR #606 head 72073976f02ca151c6ee68128175c51b069be42c. If PASS, refresh only the validated Workspace Shell runtime policy using the existing hardened upgrade path, then run the deterministic Stage 03 contract test.

## Remaining work

- Complete exact-head validation #442 for PR #606 policy head 72073976f02ca151c6ee68128175c51b069be42c.
- If PASS, produce a state-only authority snapshot binding that execution head, validate it, and rerun the existing rollback-capable Workspace Shell upgrade.
- Run tests/test_multisurrogate_dqnguard.py through research-bounded on PADataset 4c095352bfe128e93f794112741efdb7a66b9c38.
- Prepare one known-only four-class backbone target fold with 16,384 cache lineage.
- Run Architecture C smoke/small-real evaluation and validate result_record.json.

## Blockers / gates

- Stage 03 deterministic execution is blocked only on validation of the exact-path research-bounded policy correction at PR #606 head 72073976f02ca151c6ee68128175c51b069be42c.
- Do not widen research-bounded beyond tests/test_multisurrogate_dqnguard.py and do not execute Stage 03 until the validated policy is installed live.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
