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

Read the durable root provisioner state/receipt for request fd30c4c6-6756-55d1-a12d-e3cb16f50d20 without mutating or restarting anything. GitHub still shows run 39200075204/job 117891019967 queued; do not retrigger.

## Remaining work

- Read /var/lib/workspace-ci/provisioner/fd30c4c6-6756-55d1-a12d-e3cb16f50d20.json and, if present, /srv/workspace-ci/research-engine/logs/p5-fd30c4c6-6756-55d1-a12d-e3cb16f50d20-receipt.json plus runner/journal logs.
- If worker is terminal FAILED, diagnose only that exact runtime failure before any new execution decision; do not retrigger.
- If worker is active, continue following existing GitHub run 39200075204 until assignment/completion.
- After job claim/completion, close this child and return ownership upward.

## Blockers / gates

- Post-acceptance worker diagnostic: GitHub run 39200075204/job 117891019967 remains queued with no runner_name after the root provisioner returned ACCEPTED. Need durable request state and runtime receipt to determine whether the asynchronous runner worker is still active or failed before connecting.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-provisioner-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
