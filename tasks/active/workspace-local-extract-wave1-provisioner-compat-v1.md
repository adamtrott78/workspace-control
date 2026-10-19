<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-wave1-provisioner-compat-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-wave1-provisioner-compat-v1
- Title: Local EXTRACT Wave 1 provisioner compatibility
- Status: VALIDATING
- Capsule schema: v2

## Goal

Allow the already-live and already-triggered Local EXTRACT Wave 1 workload through the final root provisioner gpu-heavy compatibility guard with the smallest fail-closed change, then install that exact provisioner and recover the existing queued benchmark run without issuing another trigger.

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

Do not retrigger. Allow workspace-local-extract-wave1-runtime-compat-v1 to validate/merge/install the final privileged runtime compatibility patch, then recover existing run 39200075204.

## Remaining work

- Complete workspace-local-extract-wave1-runtime-compat-v1 and install exact merged privileged runtime.
- Resolve the existing failed deterministic request/run without a second trigger.
- After successful runner launch/claim, mark this provisioner child COMPLETE and return ownership upward.

## Blockers / gates

- Downstream privileged runtime compatibility blocker: provisioner activation and request acceptance passed, but request fd30c4c6-6756-55d1-a12d-e3cb16f50d20 failed before runner creation with RuntimeLaunchError `autonomous profile rejected: gpu-heavy`. Bounded child workspace-local-extract-wave1-runtime-compat-v1 owns the final runtime gates; do not retrigger.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-provisioner-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
