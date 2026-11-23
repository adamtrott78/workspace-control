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

Monitor exactly PA3-PA8 t007 backbone run 45273831156/job 138040300764 on lane A at PADataset PR #40 head da521eaee997c56012290c9c261ee1831432ebbc. Do not submit a duplicate. On terminal SUCCESS, require a provenance-valid artifact and known-validation acceptance (val macro-F1 >=0.95 and min-class F1 >=0.90) before freezing. Target/test/OSR evidence remains forbidden for training/checkpoint/retry selection. While the backbone runs, continue the already-frozen surrogate-selector replication/confusion-exclusion analysis. After backbone acceptance, admit exactly PA3<-PA8 and PA8<-PA3 under unchanged standard DQNGuard.

## Remaining work

- Monitor only final PA3-PA8 t007 backbone run 45273831156/job 138040300764; do not duplicate, restart, or alter the frozen PR #40 recipe while it is healthy.
- On terminal SUCCESS, validate artifact/checkpoint provenance and apply the predeclared known-validation acceptance gate: val macro-F1 >=0.95 and min-class F1 >=0.90. Target/test/OSR evidence is prohibited from checkpoint/freeze/retry selection.
- Complete the frozen surrogate-selector replication analysis: historical Rule A guard-score calibration recall, Rule B confidence geometry, Rule C feature geometry, plus the new retrospective confusion-exclusion diagnostic. Keep target-observing confusion analysis descriptive/oracle-only.
- Once a provenance-valid PA3-PA8 t007 backbone is frozen, admit exactly PA3<-PA8 and PA8<-PA3 under the unchanged standard-DQNGuard evaluator to complete the 20-cell matrix.
- After 20/20 cells are complete, report selector correlations, within-target rank quality, top-1/top-2 selection accuracy, oracle regret, and the confusion-exclusion relationship without allowing post-freeze OSR evidence to rewrite training history.

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
