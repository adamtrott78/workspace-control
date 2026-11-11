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

After parent installs validated Workspace Shell execution ca2241d44d5563b137f4c6978b33dfc060d2a968, rerun the deterministic Stage 03 contract test on PADataset 4c095352bfe128e93f794112741efdb7a66b9c38.

## Remaining work

- Wait for parent state-only authority validation and root-owned Workspace Shell refresh.
- Rerun tests/test_multisurrogate_dqnguard.py through research-bounded.
- Prepare the known-only four-class backbone target fold with cache_len=16384.
- Run Architecture C smoke/small-real evaluator and validate result_record.json.

## Blockers / gates

- PADataset source 4c095352bfe128e93f794112741efdb7a66b9c38 remains exact and clean.
- Stage 03 test execution is blocked only on installing validated Workspace Shell research runtime fix ca2241d44d5563b137f4c6978b33dfc060d2a968; the prior attempt reached Python but failed before tests because libblas.so.3 was not resolvable.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
