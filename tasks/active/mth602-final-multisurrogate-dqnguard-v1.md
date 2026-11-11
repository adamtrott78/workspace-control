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

Do not execute Stage 03 yet. Workspace-control reconciliation is complete at f51b4ee201529d8785e920458700affced52ffdf; wait for PR #606 exact V3 validation run #437 / job 130702172851. If PASS, refresh Workspace Shell PADataset authority to 4c095352bfe128e93f794112741efdb7a66b9c38 and then resume Stage 03.

## Remaining work

- Wait for PR #606 exact-head validation of reconciled workspace-control head f51b4ee201529d8785e920458700affced52ffdf.
- Wait for exact-head validation of workspace-control 50395aad06ab719b8207d9e7d3d8270a6bb35030.
- Refresh Workspace Shell to exact PADataset candidate 4c095352bfe128e93f794112741efdb7a66b9c38.
- Run tests/test_multisurrogate_dqnguard.py through research-bounded on that exact clean snapshot.
- Prepare one known-only four-class backbone target fold with 16,384 cache lineage and no target-informed checkpoint selection.
- Run architecture C smoke/small-real evaluator and validate result_record.json against the Stage 02 schema.

## Blockers / gates

- Parent reconciliation is complete; sole current gate is validation run #437 / job 130702172851, currently queued.
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
