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
- Remote branch: wave1-provisioner-compat-v1
- Remote checkpoint: f838bb35bdad72f733f0480067f52bda4f9bab7a
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Open and validate the narrow provisioner compatibility PR from wave1-provisioner-compat-v1. Require task contracts, provisioner-service regression, unit/full integration validation, and exact diff review before merge. Do not issue another Wave-1 trigger.

## Remaining work

- Open a narrow PR and require task contracts, unit regression, provisioner/service tests, and full Workspace Control validation to pass.
- Inspect exact validated diff and merge only if manifest/policy/model/runtime/workflow identities remain untouched.
- Install exact merged root provisioner through unchanged P5 bootstrap, then verify service/controller stability.
- Recover existing request fd30c4c6-6756-55d1-a12d-e3cb16f50d20 / run 39200075204 without retriggering.
- Return ownership to workspace-local-extract-wave1-controller-compat-v1 after the existing job is claimed.

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
