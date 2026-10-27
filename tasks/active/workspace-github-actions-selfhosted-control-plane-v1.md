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

Read-only incident inspection only for the already-issued maintenance command comment 6437389584. On Lambda, print `/var/lib/workspace-ci/maintenance-controller/receipts/6437389584.json` if present and bounded recent journals for `workspace-ci-maintenance-controller.service` and `workspace-ci-maintenance.service` sufficient to show processing of comment 6437389584. Do not post a second command, do not modify/delete the receipt, and do not reconcile, activate workspace-control, restart/reset any controller, or restart research-engine CPU. Return the complete read-only output.

## Remaining work

- Read only `/var/lib/workspace-ci/maintenance-controller/receipts/6437389584.json` plus the maintenance-controller/root-maintenance journal lines needed to bind the result to comment 6437389584. Do not rerun or post another command.
- If the receipt is FAILED_CLOSED because workspace-control is not ACTIVE, design the narrowest correction that allows DIAGNOSE_LANE to resolve a registered migration candidate for observation only while continuing to require ACTIVE state for RESTART_CONTROLLER and all recovery mutations; add regression/adversarial tests and fresh independent review before any retry.
- Only after a real GitHub -> L0 diagnostic receipt is durably accepted may workspace-control activation be independently gated as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- Corrected P1 bootstrap succeeded and first owner diagnose command was issued as issue #527 comment 6437389584, but static reviewed policy reveals a likely gate contradiction: DIAGNOSE_LANE derives only ACTIVE projects, while workspace-control is intentionally MIGRATION_CANDIDATE_NOT_INSTALLED / PLANNED_NOT_BOUND before activation.
- Do not issue a second maintenance command and do not activate workspace-control. First capture the durable maintenance-controller receipt for comment 6437389584 read-only. If it failed closed with the expected inactive-project rejection, treat that as a design/implementation blocker requiring a bounded reviewed correction to permit read-only diagnosis of a migration candidate without granting activation/execution authority.
- No reconciliation, controller restart/reset, research-engine CPU restart, P2/P3 change, or capacity widening is authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
