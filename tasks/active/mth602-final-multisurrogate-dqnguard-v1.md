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

Do not execute Stage 03 until the parent runtime refresh reports PASS and live Workspace Shell confirms PADataset HEAD 4c095352bfe128e93f794112741efdb7a66b9c38. After that, run the deterministic Stage 03 tests through research-bounded on that exact clean snapshot.

## Remaining work

- Wait for parent hardened multirepo runtime refresh to bind workspace-control 6466ff118127af1dfcc2dbf6aa69833fe1d06c04 and PADataset 4c095352bfe128e93f794112741efdb7a66b9c38.
- Verify PADataset exact HEAD/status/tree through live Workspace Shell.
- Run tests/test_multisurrogate_dqnguard.py through research-bounded.
- Prepare one known-only four-class backbone target fold with 16,384 cache lineage and no target-informed checkpoint selection.
- Run architecture C smoke/small-real evaluator and validate result_record.json against the Stage 02 schema.

## Blockers / gates

- Live Workspace Shell runtime has not yet been rebound to PADataset Stage 03 candidate 4c095352bfe128e93f794112741efdb7a66b9c38.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
