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
- Remote checkpoint: 7544190ff9e87e7defcd1148550e57a637a19e34
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Do not retrigger. Await/read durable worker-state evidence for accepted request fd30c4c6-6756-55d1-a12d-e3cb16f50d20; controller compatibility itself is no longer the blocker.

## Remaining work

- Allow workspace-local-extract-wave1-provisioner-compat-v1 to inspect the accepted request worker state/receipt.
- Once job 117891019967 is claimed or the exact worker failure is resolved, mark this controller child COMPLETE and return ownership to workspace-local-extract-wave1-execution-v1.

## Blockers / gates

- Downstream worker-state blocker only: controller and provisioner compatibility fixes are installed and the deterministic Wave-1 request is accepted, but GitHub job 117891019967 still has no runner assignment. Await durable root worker receipt inspection; do not retrigger.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-controller-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
