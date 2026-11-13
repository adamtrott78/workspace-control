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
- Remote checkpoint: db8e2a1a97b69b73e3602e83ebd196686ceaaa95
- Remote verified: true

## Next safe action

Install PADataset db8e2a1a97b69b73e3602e83ebd196686ceaaa95 into the live Workspace Shell authority/snapshot through the reviewed checkpoint-refresh operator, then run exact-head deterministic Stage 03 validation. Do not issue a new /lambda-scientific request until that validation passes.

## Remaining work

- Refresh the live Workspace Shell task authority and clean PADataset execution snapshot to the exact repaired head.
- Run exact-head deterministic Stage 03 contract validation through Workspace Shell and retain the receipt.
- Only on deterministic PASS, issue exactly one new frozen Stage 03 Architecture C scientific request.
- Interpret the resulting Architecture C metrics against the matching fixed-surrogate DQNGuard cell under the frozen Stage 03 contract.

## Blockers / gates

- Live Workspace Shell authority and /srv/workspace-shell/PADataset remain pinned to be04a4a4428a3c57233fc1ee598b4311ece96587; exact repaired head db8e2a1a97b69b73e3602e83ebd196686ceaaa95 is not executable until the reviewed checkpoint refresh completes.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
