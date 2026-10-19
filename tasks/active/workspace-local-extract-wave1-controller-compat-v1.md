<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-wave1-controller-compat-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-wave1-controller-compat-v1
- Title: Local EXTRACT Wave 1 controller compatibility
- Status: VALIDATING
- Capsule schema: v2

## Goal

Make the already-authorized and already-triggered Local EXTRACT Wave 1 job claimable by the existing Lambda GPU scale-set controller with the smallest fail-closed controller compatibility fix, then activate that exact controller and recover existing workflow run 39200075204 without issuing another benchmark trigger.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: wave1-controller-compat-v1
- Remote checkpoint: ca347aad4946aecbcbc8c49031cd015775d42804
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Open and validate the narrow controller compatibility PR from wave1-controller-compat-v1. Require controller unit/regression tests and Workspace Control validation to pass; inspect the diff before merge. Do not issue another Wave-1 trigger.

## Remaining work

- Open a narrow pull request and require Workspace Control validation / controller Go tests to pass.
- Inspect the validated diff and merge only if the exact controller compatibility boundary remains unchanged.
- Determine whether an already-authorized autonomous root-controller deployment route exists; use it if available, otherwise stop at the genuine root-control-plane human gate.
- Install/verify exact merged controller and recover run 39200075204 / job 117891019967 without retriggering.
- Return ownership to workspace-local-extract-wave1-execution-v1 once the existing job is claimed.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-controller-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
