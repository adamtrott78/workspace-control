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
- Remote checkpoint: 70d5668599de767647603ddec55815b9523d1bb8
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Do not retrigger. Install exact privileged runtime merge 70d5668599de767647603ddec55815b9523d1bb8 through unchanged P5 bootstrap, then recover existing run 39200075204.

## Remaining work

- Install exact runtime merge 70d5668599de767647603ddec55815b9523d1bb8 through unchanged P5 bootstrap.
- Recover the existing Wave-1 execution without a second trigger.
- After successful runner launch/claim, close the runtime/provisioner/controller support chain and return ownership upward.

## Blockers / gates

- Root runtime install gate only: runtime compatibility PR #225 is validated/merged, but installed privileged runtime must be updated before the existing Wave-1 execution can be recovered. Do not retrigger.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-provisioner-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
