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
- Remote branch: main
- Remote checkpoint: a895daaee6c744c569b45d44d72e2ea3d38df15d
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Inspect existing workspace-control deployment/control-plane routes for an authorized autonomous way to install exact merge a895daaee6c744c569b45d44d72e2ea3d38df15d as the root-owned Lambda controller. Prefer an existing trusted route; do not invent a new privilege path and do not issue another Wave-1 trigger.

## Remaining work

- Discover whether workspace-control already has an authorized autonomous deployment/control-plane route that can install the exact merged root-owned controller a895daaee6c744c569b45d44d72e2ea3d38df15d.
- If such a route exists, use it and verify exact installed controller identity/service health; otherwise stop at the genuine root-control-plane human gate rather than asking the user to execute the research workload.
- Recover existing research-engine run 39200075204 / job 117891019967 after controller activation without retriggering.
- Once the existing job is claimed, return ownership to workspace-local-extract-wave1-execution-v1.

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
