<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-wave1-provisioner-compat-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-wave1-provisioner-compat-v1
- Title: Local EXTRACT Wave 1 provisioner compatibility
- Status: IN_PROGRESS
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

Implement the smallest fail-closed provisioner patch on wave1-provisioner-compat-v1: permit gpu-heavy only when workload_class is model-eval-dual-gpu or model-eval-local-extract-wave1, and add focused service regression proving Wave 1 uses the exact existing two-GPU envelope. Preserve generic gpu-heavy DENY and all root manifest/policy identities.

## Remaining work

- Patch only scripts/lambda_ci_provisioner_service.py exact gpu-heavy workload allowlist and focused provisioner-service tests.
- Run Workspace Control validation, inspect exact diff, and merge only after PASS.
- Install exact merged root provisioner through unchanged P5 bootstrap; verify accepted manifest/policy identities remain unchanged.
- Verify GPU controller stability and that existing request fd30c4c6-6756-55d1-a12d-e3cb16f50d20 is accepted, then follow run 39200075204 without retriggering.
- Return ownership to workspace-local-extract-wave1-controller-compat-v1 after existing job claim.

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
