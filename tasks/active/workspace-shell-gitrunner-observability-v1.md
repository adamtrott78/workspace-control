<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-gitrunner-observability-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-gitrunner-observability-v1
- Title: Workspace Shell GitRunner Observability v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Widen Workspace Shell only enough to diagnose GitRunner/control-plane incidents without operator terminal relay: add exact read-only systemd inspection for selected Workspace CI controller/maintenance/v3 units and design a sanitized read-only maintenance-receipt interface, while preserving the existing ban on generic shell, generic systemctl, GitHub credentials, maintenance-socket mutation authority, sibling-project execution authority, and privileged helper widening.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-gitrunner-observability-v1
- Remote checkpoint: 1ca44e019fed66a55f2b9985d9d04397ba37b668
- Remote verified: true

## Next safe action

Start a fresh ChatGPT conversation with GitHub + Heartbeat + Workspace Shell. Recover this task plus the GitRunner task and umbrella semantic-execution task. Use task_id workspace-shell-mcp-v1 for live Workspace Shell inspect calls, then immediately read unit_logs_redacted for the legacy workspace-control controller and maintenance controller and maintenance_receipt for comments 6567987093 and 6567995530. Persist the exact diagnosis to PR #572 / GitRunner task. Do not stop after incident repair: return to umbrella task workspace-semantic-execution-migration-v1 and continue its next_safe_action.

## Remaining work

- Fresh-chat MCP schema rediscovery for unit_logs_redacted and maintenance_receipt.
- Read bounded legacy workspace-control controller journal and maintenance controller journal directly through Workspace Shell.
- Read maintenance receipts for comments 6567987093 and 6567995530.
- Determine why the legacy controller is ACTIVE/RUNNING while run 41378944347 remains queued with no runner assignment.
- Record exact root cause and bounded repair/serviceability evidence on GitRunner PR #572.
- Keep any GitRunner mutation/canary authority in the GitRunner task; observability remains diagnostic.
- After diagnosis, hand control back to umbrella semantic-execution task rather than treating this incident as the whole program.

## Blockers / gates

- The current ChatGPT conversation cached the pre-update MCP input schema, so it cannot call the newly added unit_logs_redacted or maintenance_receipt operations even though the live server's local MCP tool-schema smoke passed. A fresh chat is required for schema rediscovery.
- No additional GitRunner canary/cutover authority is implied by this observability task.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-gitrunner-observability-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
