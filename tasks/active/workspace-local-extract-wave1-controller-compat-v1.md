<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-wave1-controller-compat-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-wave1-controller-compat-v1
- Title: Local EXTRACT Wave 1 controller compatibility
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Make the already-authorized and already-triggered Local EXTRACT Wave 1 job claimable by the existing Lambda GPU scale-set controller with the smallest fail-closed controller compatibility fix, then activate that exact controller and recover existing workflow run 39200075204 without issuing another benchmark trigger.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: wave1-controller-compat-v1
- Remote checkpoint: ca347aad4946aecbcbc8c49031cd015775d42804
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Implement the smallest fail-closed controller patch on branch wave1-controller-compat-v1: add exact model-eval-local-extract-wave1 handling to GPU workload selection, /lambda-ci-local-extract-wave1 attestation command mapping, and deterministic GPU runner identity, with regression tests preserving CPU rejection and generic gpu-heavy DENY. Do not modify research-engine or issue another trigger.

## Remaining work

- Patch exact Wave-1 workload acceptance, command attestation, deterministic GPU runner mapping, and focused tests.
- Run Workspace Control validation, inspect diff, open/merge a narrow PR only after PASS.
- Determine whether an already-authorized autonomous root-controller deployment route exists; use it if available, otherwise stop at the genuine root-control-plane human gate rather than asking the user to run the research workload.
- Install/verify exact merged controller and recover run 39200075204 / job 117891019967 without retriggering.
- Return ownership to workspace-local-extract-wave1-execution-v1 once the existing job is claimed.

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
