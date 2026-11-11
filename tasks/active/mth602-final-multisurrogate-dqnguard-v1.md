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

Do not execute Stage 03 until PR #606 policy head 72073976f02ca151c6ee68128175c51b069be42c passes exact validation and the live Workspace Shell runtime is refreshed to that policy. PADataset source 4c095352bfe128e93f794112741efdb7a66b9c38 is already verified clean and ready.

## Remaining work

- Wait for the exact-path research-bounded policy correction to validate and be installed live.
- Run tests/test_multisurrogate_dqnguard.py through research-bounded.
- Prepare one known-only four-class backbone target fold with 16,384 cache lineage and no target-informed checkpoint selection.
- Run Architecture C smoke/small-real evaluator and validate result_record.json against the Stage 02 schema.

## Blockers / gates

- Live PADataset Stage 03 source binding is now exact and clean at 4c095352bfe128e93f794112741efdb7a66b9c38.
- Execution is blocked only because current research-bounded policy does not yet admit tests/test_multisurrogate_dqnguard.py; exact-path correction PR #606 head 72073976f02ca151c6ee68128175c51b069be42c is under validation #442.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
