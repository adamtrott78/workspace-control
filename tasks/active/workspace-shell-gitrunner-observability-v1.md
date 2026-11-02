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
- Remote checkpoint: 24726e194af7d1dbe379b8c49c5eaf94a39ab606
- Remote verified: true

## Next safe action

Run full hosted validation on the final updater candidate. If green, retarget PR #591 back to the accepted Workspace Shell branch and invoke the updater manually on Lambda with the exact validated head; no plugin recreation or recommissioning.

## Remaining work

- Run exact-head hosted validation for the transactional updater candidate.
- Retarget PR #591 back to workspace-shell-mcp-v1-current-main after validation.
- Apply one exact reviewed updater command on Lambda because the currently installed Workspace Shell cannot self-widen its root-owned runtime/config.
- After live update, inspect the legacy workspace-control controller and maintenance units directly through Workspace Shell.
- Use the new maintenance receipt/log visibility to finish the GitRunner incident diagnosis.
- Keep GitRunner v3 activation/canary authority separate.

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
