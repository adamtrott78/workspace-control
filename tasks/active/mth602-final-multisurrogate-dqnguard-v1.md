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

Do not execute Stage 03 until the parent upgrade from authority 3fb385039108074bef7b5d142bb4fc4781a5c9ab reports PASS and live Workspace Shell confirms PADataset HEAD 4c095352bfe128e93f794112741efdb7a66b9c38.

## Remaining work

- Wait for the parent hardened multirepo upgrade to complete successfully.
- Verify live PADataset HEAD 4c095352bfe128e93f794112741efdb7a66b9c38 through Workspace Shell.
- Run tests/test_multisurrogate_dqnguard.py through research-bounded.
- Prepare the known-only four-class backbone target fold and run Architecture C smoke/small-real evaluation.

## Blockers / gates

- Live Workspace Shell is not yet rebound to PADataset 4c095352bfe128e93f794112741efdb7a66b9c38; parent authority head 3fb385039108074bef7b5d142bb4fc4781a5c9ab is validated and ready for operator refresh.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
