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

Fresh independent exact-head re-review of corrected PR #560 only. Consume blocking review comment 6458462200 and verify BF-1 closure: detached HEAD is mandatory; the immutable reviewed source authority is pinned to `a2587410cde8ca2e077ea9228342b7651abb793d`; `scripts/lambda_ci_reconciler.py` must resolve at both that authority and current HEAD to exact reviewed blob `ee86b28412c0dff70fe79d915978fc9cd1f7cbd7`; the clean tracked-tree check remains; post-review source drift is limited to the installer, its regression file, and task-state files; and regressions reject a different clean commit paired with its own `--expected-head`, attached-branch execution, and reconciler source drift. Executable checkpoint `3661448cd50299a633b97b56695f4b75e0a05588` passed Workspace Control Validation run `40620049974` / job `122591614437` / #1066 SUCCESS. Preserve all previously accepted live transaction, exact legacy-env, sibling-material, rollback, controller-preservation, P1 CPU-only, concurrency, P2/P3, and capacity boundaries. Return `NO_BLOCKING_FINDING` or exact actionable blockers. Do not merge or mutate Lambda during review.

## Remaining work

- Obtain fresh independent exact-head re-review of corrected PR #560, consuming prior BF-1 disposition comment 6458462200.
- Require `NO_BLOCKING_FINDING` before any merge or Lambda hotfix installation; keep PR #559 open/unmerged and `main` pinned at `e8a458a8ce922ac89ad91354b29f5dc4ecbd5e91` during review.
- After any later accepted live repair, require a separate live-repair receipt review before one reviewed one-shot activation retry.
- Leave P2/P3/capacity widening, maintenance-command widening, and the separate `workspace-shell-mcp-v1` task unauthorized/paused.

## Blockers / gates

- The first reviewed one-shot activation submission was safely rejected before mutation; workspace-control remains unactivated.
- PR #560 BF-1 source-authority correction is frozen at executable checkpoint `3661448cd50299a633b97b56695f4b75e0a05588` and passed full validation run #1066, but still requires fresh independent exact-head acceptance.
- Do not merge PR #559 or PR #560, install the hotfix, retry the one-shot, start automatic reconciliation, issue maintenance commands, mutate sibling controllers/research-engine CPU, or widen P2/P3/capacity until review returns `NO_BLOCKING_FINDING`.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
