<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-selfhosted-control-plane-v1
- Title: GitHub Actions Self-Hosted Control Plane v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Eliminate routine dependence on metered GitHub-hosted runners by moving workspace-control and project CI onto bounded self-hosted Lambda execution while preserving a non-circular bootstrap authority, per-project isolation, fail-closed admission, review gates, and a clean path to GitHub organization runner groups. Also reduce operator copy/paste by making review targets and dispositions durable and GitHub-native.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 4d98555a678050e611502de1b9b8c35b4cf9c5fa
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Hold all scientific GPU execution. Capture one bounded read-only research-engine/gpu controller journal snapshot to classify the exact crash-loop error while implementing controller-reliability-hardening-v1 on branch controller-reliability-hardening-v1. No live restart/reset/reconcile/controller installation is authorized until the implementation batch passes full validation and the activation boundary is reviewed.

## Remaining work

- Complete controller reliability hardening v1 before resuming the local-reasoner GPU bakeoff.
- Classify the exact current research-engine/gpu crash-loop error from a bounded read-only journal snapshot and freeze it as regression evidence.
- Implement and validate admission ordering, recovery-state lifecycle, state-file ownership, stable restart certification, and restart-storm containment.
- Run full workspace-control validation on the complete hardening batch.
- Perform the owning workflow's final authority-sensitive activation review only once the implementation batch is stable; do not reintroduce iterative independent-review loops during ordinary implementation.

- Dogfood merged review_automation on this exact state-only closure PR: create the authority-sensitive request through the default-branch issue_comment command, obtain a fresh independent disposition, and verify the automation posts an ACCEPTED consumption receipt without operator prompt-copy plumbing.
- After dogfood acceptance, design the next steady-state/P2 tranche under a separate exact review gate; do not start the automatic reconcile-controller or widen live admission in this closure.
- Then remove routine hosted-runner dependence only after private-repository steady-state CI is proven under reviewed boundaries.
- Leave GitHub organization migration, capacity widening, maintenance-command widening, and workspace-shell-mcp-v1 paused until their own gates.

## Blockers / gates

- No live controller/runtime mutation is authorized by review_automation closure or dogfood.
- The next stage must remain separately reviewed before any automatic reconcile-controller startup, P2 admission widening, hosted-runner dependency removal, maintenance widening, capacity widening, or organization migration.
- The merged review automation must prove end-to-end request creation and disposition consumption on this state-only closure PR before routine reliance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
