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
- Remote checkpoint: 951b6987e590f9452eefaec15ba20b39e8af5bf3
- Remote verified: true

## Next safe action

Run exact-head full validation for the expanded read-only GitRunner diagnostic surface. Do not install live changes or add mutating recovery authority until this head passes.

## Remaining work

- Retarget PR #591 back to workspace-shell-mcp-v1-current-main after final state-sync validation.
- Prepare a bounded live-update procedure for the exact validated observability candidate.
- After live update under operator boundary, inspect workspace-control legacy controller, maintenance controller/service, v3 provisioner/reconciler, and v3 control-small unit state.
- Design/implement sanitized maintenance-receipt read without maintenance socket/group authority.
- Keep GitHub Actions cancellation in a GitHub/control-plane surface rather than adding generic network credentials to Workspace Shell.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-gitrunner-observability-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
