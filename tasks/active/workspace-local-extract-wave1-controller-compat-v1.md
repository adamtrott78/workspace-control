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
- Remote checkpoint: 6437ee9745468401f7c0d5daa40ea72e3be46257
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Execute bounded child task workspace-local-extract-wave1-provisioner-compat-v1. Patch only the stale root provisioner gpu-heavy workload guard and focused service tests so the already-authorized model-eval-local-extract-wave1 may use the existing gpu-heavy/two-GPU envelope; generic gpu-heavy remains DENY. Do not issue another Wave-1 trigger.

## Remaining work

- Complete bounded child task workspace-local-extract-wave1-provisioner-compat-v1: permit only the already-authorized model-eval-local-extract-wave1 alongside model-eval-dual-gpu in the root provisioner gpu-heavy guard, with fail-closed regression coverage.
- Validate/merge the provisioner compatibility fix and install the exact merged root-owned provisioner through the unchanged P5 bootstrap path.
- Verify the GPU controller stops crash-looping, the deterministic existing request is accepted, and existing run 39200075204 / job 117891019967 is claimed without retriggering.
- Then mark this controller child COMPLETE and return ownership to workspace-local-extract-wave1-execution-v1.

## Blockers / gates

- Provisioner compatibility blocker: scripts/lambda_ci_provisioner_service.py hard-codes gpu-heavy admission to model-eval-dual-gpu only. The exact Wave-1 workload is already live-enabled by root manifest/policy and reaches the provisioner correctly, but is rejected before runner launch. A bounded provisioner compatibility child task is required; do not retrigger.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-controller-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
