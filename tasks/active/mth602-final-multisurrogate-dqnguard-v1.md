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

Complete the MTH602/DQNGuard follow-on program with two scientifically separated tracks: (A) repair the published Target–Surrogate control by retraining competent leave-two-out backbones, and (B) develop single-backbone multi-surrogate OSR using a competent target-withheld four-known backbone. In parallel, finish the STFT/time-frequency representation diagnostic for the PA1↔PA4 boundary. Preserve true-target quarantine, known-only selection/threshold semantics, exact provenance, and keep OSR-method changes separate from backbone/representation changes.

## Repositories

### PADataset

- Intent: mutate
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-candidate-evidence-current-v1
- Remote checkpoint: 4469009659182c8c2f4d12d727e556f2a2995fc9
- Remote verified: true

## Next safe action

Fresh chat: read this capsule plus PADataset PR #23, PR #21, and Workspace Control PR #636. First confirm refreshed Workspace Shell exposes candidate-pytest, then run candidate-pytest on PR #23 exact SHA 4f27d00cce9ab15120d924963a5ecf049d032c52 while durable PADataset authority remains befe383fd67c8bca8d8ce370344b33c7e13cd52f. If PASS, verify receipt/unchanged authority. Next exercise PR #21 fd15238... PA1 provenance preflight from the persistent checkout and resume STFT only on PASS, preserving the first 120 overlays. Then execute Architecture-B B0 softmax3 on the strong PA2 seed0 backbone.

## Remaining work

- Fresh chat: confirm candidate-pytest exists, then run `pytest -q tests/test_cross_surrogate_dqnguard.py` at PR #23 exact head 4f27d00cce9ab15120d924963a5ecf049d032c52 under task mth602-final-multisurrogate-dqnguard-v1 while durable authority stays befe383fd67c8bca8d8ce370344b33c7e13cd52f.
- Verify candidate receipt binds durable checkpoint + candidate SHA/tree and ordinary task-bound execution still rejects the off-checkpoint SHA.
- Materialize PR #21 exact head fd15238aa369118e61b21ab714900861dbb99d2c in persistent STFT checkout; run repaired PA1 provenance preflight; resume only on PASS and skip first 120 completed overlays.
- After B unit validation, run B0 softmax3 on the strong PA2 seed0 four-known backbone; freeze winner from off-diagonal transfer before true PA2 evaluation.
- Then B1 expanded5, then B2 with bands; keep A pooled and C hybrid as matched baselines.
- Separately freeze PA1-aware known-only backbone/HPO and execute Track A corrected leave-two-out matrix.
- No merges without explicit authority.

## Blockers / gates

- Current conversation still exposes old cached Workspace Shell profile enum; fresh chat is required for candidate-pytest.
- STFT resume is gated on live repaired PA1 provenance preflight; do not restart blindly.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
