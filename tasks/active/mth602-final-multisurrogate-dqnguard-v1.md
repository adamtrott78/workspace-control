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

After operator installs authority 157aaf72e9e5761c8d7140a96d986e2e742a5a9c, verify PADataset 81ee9bf2a06949ce1e9477befe00f833248d8ea3 and rerun the deterministic contract test.

## Remaining work

- Wait for parent operator root refresh.
- Rerun deterministic Stage 03 test through research-bounded.
- Prepare known-only backbone with cache_len=16384.
- Run Architecture C small-real evaluation on sanctioned PyTorch-capable compute and validate result_record.json.

## Blockers / gates

- Deterministic-smoke source 81ee9bf2a06949ce1e9477befe00f833248d8ea3 is prepared and bound in validated parent authority 157aaf72e9e5761c8d7140a96d986e2e742a5a9c but is not yet installed live.
- Real Architecture C execution will require a sanctioned PyTorch-capable scientific compute surface; Workspace Shell remains intentionally bounded.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
