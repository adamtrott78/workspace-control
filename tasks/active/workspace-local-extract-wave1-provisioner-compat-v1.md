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
- Remote checkpoint: 958d6f8ed0989b2846d04b3bd3eb2ace41f5372c
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Do not retrigger. Execute the runtime child's authorized root install + prelaunch re-arm for request fd30c4c6-6756-55d1-a12d-e3cb16f50d20, preserving failed-state evidence.

## Remaining work

- Allow runtime child to install 70d5668599de767647603ddec55815b9523d1bb8 and perform the one authorized prelaunch state re-arm.
- After same job is successfully re-provisioned, mark this provisioner child COMPLETE and return ownership upward.

## Blockers / gates

- Root runtime install + evidence-preserving prelaunch re-arm gate. Runtime fix is merged; same deterministic request is terminal FAILED only because of the old prelaunch runtime guard. Recovery must archive failure state before clearing the single active request entry; no new trigger.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-provisioner-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
