<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-final-multisurrogate-dqnguard-v1
- Title: MTH 602 final project / PADataset multi-surrogate DQNGuard
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Provide Workspace Shell authority for the PADataset multi-surrogate DQNGuard project so Stage 00 can recover canonical MILCOM baseline/runtime provenance directly from the prepared Lambda checkout before architecture implementation.

## Repositories

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 4c095352bfe128e93f794112741efdb7a66b9c38
- Remote verified: true

## Next safe action

After the operator installs validated Workspace Shell execution 72073976f02ca151c6ee68128175c51b069be42c from authority 2ea84019e40de2a3d2a8fa46427af6b4ff7fe3da, verify PADataset 4c095352bfe128e93f794112741efdb7a66b9c38 live and immediately run the Stage 03 deterministic contract test.

## Remaining work

- Wait for the parent operator-owned live policy refresh to report PASS.
- Verify live PADataset exact HEAD/status/tree.
- Run tests/test_multisurrogate_dqnguard.py through research-bounded.
- Prepare the known-only backbone and run Architecture C smoke/small-real evaluation.

## Blockers / gates

- Stage 03 source 4c095352bfe128e93f794112741efdb7a66b9c38 is already exact and clean.
- Execution waits only for operator-owned Workspace Shell policy refresh to validated workspace-control execution 72073976f02ca151c6ee68128175c51b069be42c; connected Workspace Shell cannot perform the root mutation because no privileged helper authority is admitted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
