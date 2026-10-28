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

Begin the review_automation engineering tranche only; do not mutate Lambda or live controllers. Inspect existing durable review/request conventions and GitHub tooling in workspace-control, freeze a bounded design for automatic review-request creation and disposition consumption, and implement/tests on a dedicated branch. The design must bind exact task/PR/head/blob identities, reject edited/stale/wrong-head/ambiguous dispositions, preserve fresh independent reviewer semantics for authority-sensitive changes, and remove routine operator copy/paste. P2, automatic reconcile-controller startup, capacity widening, maintenance widening, and organization migration remain unauthorized.

## Remaining work

- Design and implement review_automation as the next active tranche: durable review request objects/comments, exact target/head/blob binding, automatic discovery/consumption of reviewer dispositions, duplicate/edited/stale/ambiguous fail-closed behavior, and a no-self-approval rule for authority-sensitive changes.
- Add regressions proving author/self-review cannot satisfy independent-review gates, stale or moved heads cannot be consumed, duplicate matching authority/disposition comments fail closed where ambiguity matters, and accepted exact reviews can be consumed without operator copy/paste.
- Independently review the exact review_automation implementation before using it as authority for later control-plane gates.
- After review_automation acceptance, continue P2 automatic pull_request/push admission and steady-state hosted-runner removal under separately reviewed gates.
- Leave GitHub organization migration, capacity widening, maintenance-command widening, and the separate workspace-shell-mcp-v1 task paused until their own gates.

## Blockers / gates

- P1 live activation is closed and validated. Do not perform another one-shot retry, start the automatic reconcile-controller, issue maintenance commands, restart/reset live project controllers, or widen P2/P3/capacity as part of closure.
- review_automation is now the active tranche. It must preserve independent review semantics and must not allow the authoring chat/process to self-approve authority-sensitive changes.
- Do not begin P2 automatic pull_request/push admission, steady-state hosted-runner removal, or GitHub organization migration until review_automation receives its own reviewed acceptance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
