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

Fresh independent corrected-head activation-boundary re-review of PR #558 only. Consume blocking comment 6451020368. Verify BF-1 closure: the one-shot request carries exact reviewed restart/enable/preserve sets; root reconciliation derives its actual controller delta and fails closed before receipt/policy/controller mutation if any sibling env/drop-in drift widens the restart set; request identity is bound to the expected transaction. Verify BF-2 closure: dedicated workspace-ci-reconcile-controller-once.service is Type=oneshot, no Restart=, no [Install], exact ExecStart includes --once plus exact expected transaction arguments, and preserves the polling daemon's least-privilege systemd sandbox. Verify the source-bound boundary installer installs only updated root/controller plus the static one-shot unit, never starts automatic/one-shot reconciliation, preserves automatic-controller freeze/workspace-control dormancy/sibling snapshots, restarts only root reconciler non-propagating, and rolls back exact prior bytes/unit on failure. Regression-check activation policy, BF-1/BF-2/BF-3 reconciler semantics, successful-bootstrap provenance, CPU-only/concurrency limits, no P2/P3/capacity widening. Return NO_BLOCKING_FINDING or exact actionable blockers. Do not merge or mutate Lambda during review.

## Remaining work

- Obtain fresh independent exact-head review of PR #545, focused on source provenance, exact old installed digest binding, preservation of failed receipt/cursor, candidate dormancy, project-controller preservation, the single root-maintenance service restart mutation, bounded socket readiness, and rollback restoration.
- After accepted merge, run the reviewed installer exactly once from its exact merge SHA and inspect the complete hotfix receipt before any maintenance retry.
- Only after installer PASS, post exactly one new owner `/workspace-ci-maintain diagnose workspace-control cpu` command and prove a durable COMPLETED observation-only receipt; do not reuse failed comment 6437389584.
- Only after the diagnostic receipt is accepted may workspace-control activation be independently gated as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- PR #558 remains review-only and unmerged pending fresh independent corrected-head activation-boundary review of BF-1/BF-2 closure.
- The new root/controller/one-shot boundary is validated in source but not yet installed on Lambda.
- Do not merge PR #558, install the submission boundary, reconcile/activate workspace-control, start the automatic reconcile-controller, issue maintenance commands, restart/reset preserved project controllers, restart research-engine CPU, or widen P2/P3/capacity before corrected-head review returns NO_BLOCKING_FINDING.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
