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
- Remote checkpoint: c1ced4f1681b068b9bf4bf8bde5edc9efd6f25a4
- Remote verified: true

## Next safe action

Open a draft PR and run exact-head hosted validation. If green, design the sanitized maintenance-receipt read path as a separate read-only boundary; do not install live changes until the exact validated head is explicitly bound for Workspace Shell update.

## Remaining work

- Expand exact read-only unit allowlist.
- Add regression tests proving authorized CI units are readable and unrelated units remain denied.
- Design/implement sanitized maintenance-receipt read without maintenance socket/group authority.
- Run hosted validation.
- Only after exact-head validation, prepare bounded live update that preserves accepted Workspace Shell transport and least privilege.

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
