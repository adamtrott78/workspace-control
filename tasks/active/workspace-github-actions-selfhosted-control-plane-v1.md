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

Fresh independent exact-head re-review of the PR #560 persisted rejected-marker schema correction only, after this task-state-only finalization passes validation. Consume prior NO_BLOCKING_FINDING/authority comment 6459375605 and failed-live incident comment 6459677642. Verify executable checkpoint 171ac7afb554e4ae81f979bc91286e3f4d2b615d changes only the installer/test, removes only the nonexistent top-level last-rejected status assumption, continues to require exact nested response.status=REJECTED, ReconcileError, exact request/policy/workflow/error bindings, and derives receipt status from the nested response. Verify the test fixture now matches the exact reconcile-controller persisted state schema and rejects nested response status drift. Preserve the external exact-head/exact-installer authority gate, detached/clean source checks, exact reconciler blob, installed binary/file baselines, exact sibling env/drop-in preflight, root-only non-propagating mutation, post-certification marker archival, exact rollback, automatic/one-shot/workspace/sibling preservation, P1 CPU-only/maxRunners=1/concurrency=1, and P2/P3/capacity/maintenance boundaries. Workspace Control Validation run 40625286178 / job 122608624246 / #1074 is SUCCESS. Return NO_BLOCKING_FINDING or exact actionable blockers. If NO_BLOCKING_FINDING, post a new exact unedited authority block for the final reviewed head/blob. Do not merge or mutate Lambda during review.

## Remaining work

- Obtain a fresh independent exact-head re-review of corrected PR #560 after task-state-only finalization. The reviewer must consume prior acceptance 6459375605 and failed-live incident receipt 6459677642, verify the real persisted last-rejected schema correction, and confirm all previously accepted provenance/mutation/preservation guarantees remain intact.
- If and only if the reviewer returns NO_BLOCKING_FINDING, require exactly one new unedited WORKSPACE_CONTROL_PRIVILEGED_INSTALL_REVIEW_V1 authority block binding the new exact PR #560 head, corrected installer Git blob, exact reconciler blob ee86b28412c0dff70fe79d915978fc9cd1f7cbd7, prior blocking comment 6459054952, and the exact new review-request comment ID.
- Keep PR #559 open/unmerged and main pinned at e8a458a8ce922ac89ad91354b29f5dc4ecbd5e91. Any PR #560 head/blob change after the next accepted authority receipt requires another fresh review/authority receipt.
- After a later successful reviewed live repair, require a separate live-repair receipt review before one reviewed deterministic one-shot activation retry; do not retry or activate as part of the installer review phase.
- Leave P2 automatic pull_request/push admission, P3 organization migration, capacity widening, maintenance-command widening, and the separate workspace-shell-mcp-v1 task unauthorized/paused.

## Blockers / gates

- The first reviewed one-shot activation submission remains safely rejected before mutation; workspace-control remains unactivated.
- The previously accepted PR #560 live hotfix attempt from head 9bfe7bb6ddd7793c398c4b1ccfcdf98818c65141 failed closed before mutation because the installer/test fixture modeled a nonexistent top-level last-rejected status field; durable incident comment 6459677642 records the exact failure and no-mutation boundary.
- The persisted-schema correction is fully validated at executable checkpoint 171ac7afb554e4ae81f979bc91286e3f4d2b615d / run #1074, but changing the installer/head invalidates prior authority comment 6459375605 for execution. Fresh independent exact-head acceptance plus a new unedited exact external authority block is required before another live install attempt.
- Do not merge PR #559 or PR #560, do not rerun the installer, archive the rejected marker, retry the one-shot, start the automatic reconcile-controller, issue maintenance commands, manually start/enable workspace-control CPU, restart/reset siblings, restart research-engine CPU, or widen P2/P3/capacity until the fresh review gate is satisfied.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
