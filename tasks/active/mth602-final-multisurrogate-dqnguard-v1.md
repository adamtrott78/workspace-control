<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

## Task

- ID: mth602-final-multisurrogate-dqnguard-v1
- Title: MTH 602 final project / PADataset multi-surrogate DQNGuard
- Status: IN_PROGRESS

## Next safe action

Monitor exactly PA8<-PA3 replacement run 45444347242/job 138623859746 on lane B (`padataset-scientific-single-gpu-2-v1`) at frozen PR54 head f1256048b51fd863ad3fb46f9c547eff401016e7. Do not duplicate. At terminal SUCCESS validate the result artifact/provenance, close the 20/20 directional matrix, and finalize Rule A/confusion-exclusion statistics. Diagnose/fix lane A separately after the final OSR is safely running/completed; do not hand-edit root/controller ledger state.

## Remaining work

- Monitor only lane-B PA8<-PA3 replacement run 45444347242/job 138623859746; do not duplicate, restart, or change its frozen config.
- At terminal SUCCESS, validate result artifact/provenance and close the 20/20 t007 directional matrix.
- Finalize Rule A and retrospective confusion-exclusion correlations/ranking/regret on all 20 cells.
- Only after the OSR lane is idle, execute frozen historical Rule B confidence-geometry and Rule C feature-geometry replication to avoid host CPU contention.
- Diagnose/fix lane A controller/root-ledger reconciliation separately. Preserve authority boundaries: no manual root-record edits and no unreviewed controller mutation.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
