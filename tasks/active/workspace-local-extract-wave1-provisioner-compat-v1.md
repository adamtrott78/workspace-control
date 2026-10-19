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
- Remote checkpoint: 9393dd2ad27c30d3a0db5d8e0f537a311f015d96
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

At the genuine root-control-plane boundary, install exact workspace-control merge 9393dd2ad27c30d3a0db5d8e0f537a311f015d96 through unchanged scripts/bootstrap_lambda_ci_p5.sh. Verify manifest/policy identities remain unchanged and the GPU controller has zero restart delta after activation. Then resume ChatGPT/GitHub control on existing run 39200075204; do not retrigger.

## Remaining work

- Install exact provisioner compatibility merge 9393dd2ad27c30d3a0db5d8e0f537a311f015d96 through the unchanged root-owned P5 bootstrap; no autonomous privileged deploy workflow exists.
- Verify accepted manifest/policy blobs are unchanged and all three control-plane services are active.
- Verify GPU-controller restart count is stable after activation and the stale provisioner rejection no longer recurs.
- Confirm existing deterministic request fd30c4c6-6756-55d1-a12d-e3cb16f50d20 is accepted and run 39200075204 / job 117891019967 is claimed without retriggering.
- Return ownership to workspace-local-extract-wave1-controller-compat-v1 after job claim.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-provisioner-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
