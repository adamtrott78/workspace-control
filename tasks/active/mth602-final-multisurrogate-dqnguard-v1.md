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

Matched control design is frozen and validated at PADataset draft PR #56 head d955a244f7cfd8bfd6cbc4e5ca9ba9c38a23a82d. Next implement the bounded control evaluator/request path against that exact frozen plan, preserving DQN-IDS-style softmax3 hard-action semantics with 625 known + 625 external-surrogate validation and historical VarMax surrogate_all+smoke semantics. Validate the implementation and all 20 requests before any control admission; do not retrain backbones or use target/test/OSR evidence for fitting, method selection, retry policy, or control redefinition.

## Remaining work

- Implement and validate the bounded matched-control evaluator/request path frozen by PADataset PR #56. DQN-IDS-style must use the external-surrogate validation split, never target-open; VarMax must remain historical surrogate-all and must not consume the external surrogate.
- Execute the matched control matrix only after implementation/request validation closes, then report per-cell/aggregate DQNGuard-minus-control deltas rather than comparing repaired DQNGuard against paper-era control numbers.
- Execute final multi-seed robustness only after the control matrix closes: repeat the frozen backbone/method recipes across the predetermined seed set, report mean/std and confidence intervals, surrogate-winner frequency, oracle-regret distributions, same-backbone directional asymmetry stability, and whether Rule A/B/C/confusion-exclusion relationships survive seeds.
- Complete final scientific synthesis comparing paper-era versus repaired geometry, matched controls, and seeded robustness without allowing post-hoc target/test evidence to rewrite training/checkpoint/threshold history.

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
