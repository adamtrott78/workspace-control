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

Fresh independent exact-head review of PR #560 only. Verify the safe rejection occurred before mutation and BF-1 behaved correctly. Verify the root cause is precisely the historical sibling env encoding that omits only WORKSPACE_CI_CONTROLLER_STATE_ROOT while the exact installed reviewed Go controller binary defaults that variable to /var/lib/workspace-ci/controller/state. Verify the reconciler admits only exact current bytes or exact legacy bytes for the same manifest/lane and still treats every other env/drop-in difference as restart-requiring. Verify APPLY does not rewrite preserved legacy sibling env bytes. Verify the source-bound hotfix installer fail-closes unless the exact rejected request/policy/workflow, exact current installed digests, exact failed one-shot generation, exact controller binary, exact service snapshots, all four exact legacy env files, and all four exact 134.88.12.0/22 drop-ins are present; forward mutation is root reconciler only plus non-propagating root restart; the exact rejected marker is archived only after certification to permit one deterministic retry; rollback restores exact root and rejected-marker bytes and exact service generations. Return NO_BLOCKING_FINDING or exact actionable blockers. Do not merge or mutate Lambda during review.

## Remaining work

- Obtain fresh independent exact-head review of PR #545, focused on source provenance, exact old installed digest binding, preservation of failed receipt/cursor, candidate dormancy, project-controller preservation, the single root-maintenance service restart mutation, bounded socket readiness, and rollback restoration.
- After accepted merge, run the reviewed installer exactly once from its exact merge SHA and inspect the complete hotfix receipt before any maintenance retry.
- Only after installer PASS, post exactly one new owner `/workspace-ci-maintain diagnose workspace-control cpu` command and prove a durable COMPLETED observation-only receipt; do not reuse failed comment 6437389584.
- Only after the diagnostic receipt is accepted may workspace-control activation be independently gated as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- The first reviewed one-shot activation submission was safely rejected before mutation; workspace-control remains unactivated.
- PR #560 strict legacy-env equivalence correction is validated but requires fresh independent exact-head review before any live hotfix install.
- Do not merge PR #559 or PR #560, do not install the hotfix, do not retry the one-shot, do not start the automatic reconcile-controller, issue maintenance commands, manually start/enable workspace-control CPU, restart/reset siblings, restart research-engine CPU, or widen P2/P3/capacity until independent review returns NO_BLOCKING_FINDING.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
