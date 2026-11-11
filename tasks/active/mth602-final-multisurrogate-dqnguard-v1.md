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

Do not execute MTH602 Stage 03. Parent recovery is gated on independent review of PR #604 request 6802353544 for exact live transaction head 1a355725c7ff80434622696995fcb72c5c9812f7; after accepted/consumed review, execute the bounded transaction once, finish exact-head workspace-control validation 50395aad06ab719b8207d9e7d3d8270a6bb35030, then refresh Workspace Shell PADataset to 4c095352bfe128e93f794112741efdb7a66b9c38.

## Remaining work

- Wait for parent PR #604 live-transaction review request 6802353544, then the separately authorized one-time V3 repair.
- Wait for exact-head validation of workspace-control 50395aad06ab719b8207d9e7d3d8270a6bb35030.
- Refresh Workspace Shell to exact PADataset candidate 4c095352bfe128e93f794112741efdb7a66b9c38.
- Run tests/test_multisurrogate_dqnguard.py through research-bounded on that exact clean snapshot.
- Prepare one known-only four-class backbone target fold with 16,384 cache lineage and no target-informed checkpoint selection.
- Run architecture C smoke/small-real evaluator and validate result_record.json against the Stage 02 schema.

## Blockers / gates

- Parent workspace-shell-multirepo-research-v1 is blocked on fresh independent authority-sensitive review of PR #604 head 1a355725c7ff80434622696995fcb72c5c9812f7 via request 6802353544; no live transaction execution is authorized yet.
- Live Workspace Shell PADataset runtime remains behind Stage 03 candidate 4c095352bfe128e93f794112741efdb7a66b9c38; no Stage 03 execution is authorized until the parent control-plane gate clears and the runtime refresh is validated.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
