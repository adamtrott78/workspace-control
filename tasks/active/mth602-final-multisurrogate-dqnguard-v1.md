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

Execute a rigorous MTH602-to-journal research program centered on backbone competence (H1), then resolve whether surrogate transfer remains intrinsically target-dependent or becomes target-blind-selectable (H2/H4), test multi-surrogate DQNGuard if needed (H5), and treat STFT representation as a bounded lower-priority ablation (H3). Preserve true-target quarantine, standard-DQNGuard controls, exact provenance, explicit seed separation, and a deadline-triggered pivot to complete MTH602 deliverables before December or the course due date.

## Next safe action

Operator is cancelling queued PA8<-PA3 workflow run 45434902484/job 138589937033 on lane A. First verify GitHub reports that exact run terminal CANCELLED. Only then admit exactly one replacement on lane B using `/lambda-scientific-2 f1256048b51fd863ad3fb46f9c547eff401016e7 l2o_directional_eval:manifests/configs/l2o_directional_eval_v1/PA3-PA8__targetPA8__surPA3.json`. Record the new run/job binding durably, monitor it to terminal, validate its provenance-valid result artifact, and close the 20/20 matrix. After the replacement is safely running/completed, diagnose and repair lane A separately without hand-editing root state or duplicating scientific admissions.

## Remaining work

- Verify operator cancellation of PA8<-PA3 run 45434902484/job 138589937033; do not re-admit while it is merely queued/cancelling.
- After exact run 45434902484 is terminal CANCELLED, admit PA8<-PA3 exactly once on lane B with `/lambda-scientific-2` at frozen PR54 head f1256048b51fd863ad3fb46f9c547eff401016e7 and the unchanged PA3-PA8__targetPA8__surPA3 config.
- Persist the replacement run/job/lane binding in the durable capsule; monitor only that replacement to terminal and validate result provenance.
- Close the 20/20 t007 directional matrix, then finalize Rule A and confusion-exclusion statistics on all 20 cells.
- Only after the OSR lane is idle, execute the frozen historical Rule B confidence-geometry and Rule C feature-geometry replication to avoid host CPU contention.
- Diagnose/fix the lane-A controller/root-ledger reconciliation separately after the final OSR is safe on lane B. Preserve authority boundaries: no manual root-record edits, no duplicate admission, no recipe/checkpoint/threshold changes.

## Blockers / gates

- Operator cancellation of queued lane-A run 45434902484 must be observed as terminal CANCELLED before the lane-B replacement may be admitted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-final-multisurrogate-dqnguard-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
