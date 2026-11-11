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
- Remote checkpoint: 81ee9bf2a06949ce1e9477befe00f833248d8ea3
- Remote verified: true

## Next safe action

After parent installs workspace-control f7ed7305e904ec24a444f7a488ca07e9bef4fdc7 and PADataset 81ee9bf2a06949ce1e9477befe00f833248d8ea3, rerun the deterministic Stage 03 contract test.

## Remaining work

- Wait for parent combined authority validation and root refresh.
- Rerun tests/test_multisurrogate_dqnguard.py through research-bounded.
- Prepare one known-only four-class backbone target fold with cache_len=16384.
- Run Architecture C small-real evaluation on a sanctioned PyTorch-capable scientific compute surface and validate result_record.json.

## Blockers / gates

- Live execution is still on PADataset 4c095352bfe128e93f794112741efdb7a66b9c38; deterministic-smoke refinement 81ee9bf2a06949ce1e9477befe00f833248d8ea3 is not installed yet.
- Workspace Shell intentionally remains a bounded deterministic-test surface rather than a PyTorch scientific runtime.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
