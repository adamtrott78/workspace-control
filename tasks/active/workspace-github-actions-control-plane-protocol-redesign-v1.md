<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-control-plane-protocol-redesign-v1
- Title: GitHub Actions Control-Plane Protocol Redesign v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Replace the current parser-chained GitHub Actions runner admission path with a formally modeled, versioned, typed control-plane protocol whose routing, authority, scheduling, provisioning, execution, recovery, and lifecycle semantics are explicit end-to-end, so any executor request admitted by policy cannot later be falsely rejected by a downstream parser that implements a different grammar.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 7d138b900944b1138a74f7d92c2db1b6e8d25ba7
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 6165556086b73d2076f205f11ec7b988150f23dd
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 35e6f451fe36f039b5f6461f7469f0eed1e79e43
- Remote verified: true

## Next safe action

Apply the exact validated single-file maintenance-controller hotfix from scripts/lambda_ci_maintenance_controller_live_update_v1.py at the final validated branch head. This is the only remaining manual root bootstrap boundary for the current parser repair; the updater verifies the old installed Git blob, replaces only /opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py, restarts only workspace-ci-maintenance-controller.service, performs two stable-running samples, and rolls back automatically on failure. After PASS, ChatGPT should immediately verify the service via Workspace Shell, post a new reset-stale command for quarantine receipt ab2334ab-384c-4432-ab84-f5b38ba4071d, consume the maintenance receipt, and continue the v3 migration.

## Remaining work

- Pass full repository validation for the RFC3339 nanosecond maintenance timestamp fix and freeze its exact source/blob.
- Establish the smallest durable Workspace Shell reviewed-helper bootstrap/update path needed to install exact root-owned GitRunner maintenance/cutover helpers without future plugin schema changes; preserve empty-by-default generic authority and never expose generic bash/systemctl.
- Install only the validated maintenance-controller fix on Lambda, restart only the maintenance controller if required, and prove service health.
- Re-run reset-stale against quarantine receipt ab2334ab-384c-4432-ab84-f5b38ba4071d; require fresh scale-set ID, two zero-state observations, and READY_FOR_SINGLE_RETRY with automatic_workflow_triggered=false.
- Contain/cancel stale run 41378944347 through the correct scheduler/control-plane mechanism and separately prove legacy Lambda-side runner/JIT/reservation/process cleanup and old scale-set assigned/running counts zero.
- Prepare and execute migration-order #2 padataset-cpu-public-v1 canary under a NEW separately validated one-shot ACTIVATE_ONE_V3_CANARY authority.
- Prepare and execute migration-order #3 padataset-gpu-single-public-v1 canary under its own NEW separately validated one-shot authority.
- After active-class canaries pass, execute the single production generation cutover and retire v2 under the migration plan.
- Keep research-cpu-public-v1 separately gated and all Research GPU-derived classes NO_BY_DEFAULT.

## Blockers / gates

- Current incident gate: legacy workspace-control route has a queued job 41378944347 with no runner assignment even though workspace-ci-controller@workspace-control-cpu.service is ACTIVE/RUNNING. Exact journal/maintenance-receipt evidence requires a fresh ChatGPT conversation because the current chat cached the pre-update MCP schema.
- Run 41378944347 became stale after PR #590 advanced; do not use it as a clean serviceability probe once controller recovery occurs. A correct exact-head attestor may reject it.
- Further live v3 migration still requires a new separately bound one-shot canary authority per class, beginning with padataset-cpu-public-v1.
- Research CPU activation remains separately gated.
- All Research GPU-derived runner classes remain inherited-contained and NO_BY_DEFAULT.
- Research Engine PR #283 remains draft/proposal-only; no default-branch producer cutover is authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
