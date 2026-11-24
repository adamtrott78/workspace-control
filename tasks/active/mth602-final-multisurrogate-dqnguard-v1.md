<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

## Task

- ID: mth602-final-multisurrogate-dqnguard-v1
- Title: MTH 602 final project / PADataset multi-surrogate DQNGuard
- Status: IN_PROGRESS

## Current scientific checkpoint

- Final t007 directional matrix: **20/20 CLOSED**
- Final cell: PA8<-PA3, lane B run `45444347242` / job `138623859746` = SUCCESS
- Result artifact: `14945842346`, digest `sha256:34dac735ef37d788e956c89b91478ca0c0a07a346a789320970d1c52fc69ed01`
- U-F1: `0.9074289030760302`; AUROC: `0.9227523467878138`; known reject: `0.0634320053416425`
- Provenance: scientific receipt PASS; target labels not used for tuning; threshold source known-only; no recipe/checkpoint/retry feedback

## Next safe action

Hold lane-A mutation at the authority gate. Fix lane A only if an already-reviewed recovery path with exact current-state authority becomes available. Do not hand-edit controller/root ledgers, reuse exact-job historical repair scripts outside their bindings, or widen Workspace Shell authority. Per operator sequencing, do not start Rule A/B/C analysis until lane A is resolved.

## Remaining work

- Resolve lane-A recovery authority gate using an already-reviewed path only.
- After lane A is healthy, finalize Rule A and retrospective confusion-exclusion correlations/ranking/regret on all 20 cells.
- Only after lane A recovery is complete and OSR execution is idle, execute frozen historical Rule B confidence-geometry and Rule C feature-geometry replication.
- Compare historical vs repaired selector behavior and distinguish target-blind deployable metrics from target-aware retrospective mechanism diagnostics.

## Blockers / gates

- LANE_A_RECOVERY_AUTHORITY_GATE: final t007 OSR is complete, but connected Workspace Shell cannot inspect the scientific controller unit (`UNIT_NOT_AUTHORIZED`), the live maintenance `reset-stale` path is explicitly limited to workspace-control/cpu, and no reviewed helper/approval in the durable task targets the current lane-A controller/root-ledger state. Historical PR #593/#594 ledger repairs are exact-job bounded and cannot be repurposed. Do not hand-edit ledgers, widen Workspace Shell authority, or invent a new root action.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
