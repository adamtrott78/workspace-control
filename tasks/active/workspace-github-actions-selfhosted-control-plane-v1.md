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

Fresh independent exact-head review of PR #551 only. Review exact code/test checkpoint b57fb768e5f17eeb706059ef3ff0ed81523b012a and the final PR head, verifying the checkpoint-to-head delta is task-state-only. Verify candidate->ACTIVE workspace-control reconciliation restarts only workspace-ci-controller@workspace-control-cpu.service; unchanged ACTIVE research-engine/PADataset controllers are preservation-only with exact before/after systemd snapshots; explicit controller-config drift becomes an explicit restart delta; unchanged sibling policy/config files are not rewritten unnecessarily; and research-engine CPU can remain inactive/dead NRestarts=12411 despite registry ACTIVE. Verify the source-bound hotfix installer binds the exact old installed reconciler digest c424e62c20cd38fa0380d315e4cf28831ce63ff63dd7aa9711913a41c405fcc6, successful diagnose receipt/cursor 6438723476, workspace-control dormancy, frozen workspace-ci-reconcile-controller.service, and project-controller baselines; replaces only the reconciler Python file; restarts only workspace-ci-reconciler.service with --job-mode=ignore-dependencies; proves live socket readiness; and restores exact prior bytes with the same preservation proofs on rollback. Return NO_BLOCKING_FINDING or exact actionable blockers. Do not merge or mutate Lambda during review.

## Remaining work

- Obtain fresh independent exact-head review of PR #545, focused on source provenance, exact old installed digest binding, preservation of failed receipt/cursor, candidate dormancy, project-controller preservation, the single root-maintenance service restart mutation, bounded socket readiness, and rollback restoration.
- After accepted merge, run the reviewed installer exactly once from its exact merge SHA and inspect the complete hotfix receipt before any maintenance retry.
- Only after installer PASS, post exactly one new owner `/workspace-ci-maintain diagnose workspace-control cpu` command and prove a durable COMPLETED observation-only receipt; do not reuse failed comment 6437389584.
- Only after the diagnostic receipt is accepted may workspace-control activation be independently gated as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- P1 activation remains blocked until fresh independent review accepts the exact activation-delta reconciler correction and bounded installer.
- The currently installed Lambda reconciler still has the old restart-all-ACTIVE behavior; do not reconcile or activate before the reviewed hotfix is installed and its live receipt is accepted.
- Do not restart/reset project controllers, restart research-engine CPU, issue further maintenance commands, or widen P2/P3/capacity.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
