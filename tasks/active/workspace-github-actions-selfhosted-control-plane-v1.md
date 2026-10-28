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

Fresh independent exact-head re-review of corrected PR #560 only. Consume blocking review comment 6459054952. Verify the residual BF-1 is closed by moving privileged execution authority outside caller-controlled HEAD: the installer still requires caller HEAD equality, detached HEAD, a clean tracked tree, tracked helper/reconciler paths, and exact reconciler blob ee86b28412c0dff70fe79d915978fc9cd1f7cbd7, but before any live preflight or mutation it additionally fetches public GitHub PR #560 comments without reading credentials and requires exactly one unedited OWNER-authored WORKSPACE_CONTROL_PRIVILEGED_INSTALL_REVIEW_V1 authority receipt. That receipt must bind task workspace-github-actions-selfhosted-control-plane-v1, PR 560, the exact current HEAD, exact current installer Git blob, exact reconciler blob, prior blocking comment 6459054952, a prior unedited fresh exact-head review-request comment that itself names the same HEAD, and disposition NO_BLOCKING_FINDING. Missing, edited, malformed, stale, or ambiguous authority fails closed. Verify the required regression specifically models a different clean descendant whose only changed privileged identity is the installer blob, pairs it with its own --expected-head, leaves the reconciler blob unchanged, and proves rejection because the external authority binds the prior reviewed head/blob. Preserve every previously accepted exact legacy-env, sibling-material, transaction, root-only non-propagating mutation, rejected-marker ordering/rollback, controller freeze/dormancy, sibling preservation, P1 CPU-only/maxRunners=1/concurrency=1, and P2/P3/capacity boundary. Executable checkpoint df9d8f2d74f905f7540408430c0f668b8186b31f passed Workspace Control Validation run 40622676196 / job 122600179745 / #1072 SUCCESS. Return NO_BLOCKING_FINDING or exact actionable blockers. If NO_BLOCKING_FINDING, durably record the exact authority block required by the installer in the same PR #560 review comment. Do not merge or mutate Lambda during review.

## Remaining work

- Obtain a fresh independent exact-head re-review of corrected PR #560, consuming blocking review comment 6459054952 and the exact new review request.
- If and only if the reviewer returns NO_BLOCKING_FINDING, require the reviewer to durably post exactly one unedited WORKSPACE_CONTROL_PRIVILEGED_INSTALL_REVIEW_V1 authority block binding the exact reviewed PR #560 head, exact installer Git blob, exact reconciler Git blob, prior blocking comment 6459054952, and exact review-request comment ID. Any different head/blob or edited/ambiguous authority remains fail-closed.
- Keep PR #559 open/unmerged and main pinned at e8a458a8ce922ac89ad91354b29f5dc4ecbd5e91. Do not change PR #560 head after an accepted authority receipt; any head change requires a fresh review/authority receipt.
- After later accepted live repair, require a separate live-repair receipt review before one reviewed one-shot activation retry; do not retry or activate as part of this correction/re-review phase.
- Leave P2 automatic pull_request/push admission, P3 organization migration, capacity widening, maintenance-command widening, and the separate workspace-shell-mcp-v1 task unauthorized/paused.

## Blockers / gates

- The first reviewed one-shot activation submission was safely rejected before mutation; workspace-control remains unactivated.
- PR #560 residual BF-1 from independent review comment 6459054952 is corrected and fully validated at executable checkpoint df9d8f2d74f905f7540408430c0f668b8186b31f, but the corrected exact head still requires fresh independent acceptance and an exact external review-authority receipt before any live hotfix installation.
- Do not merge PR #559 or PR #560, do not install the hotfix, archive the rejected marker, retry the one-shot, start the automatic reconcile-controller, issue maintenance commands, manually start/enable workspace-control CPU, restart/reset siblings, restart research-engine CPU, or widen P2/P3/capacity until independent review returns NO_BLOCKING_FINDING with the exact authority block required by the installer.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
