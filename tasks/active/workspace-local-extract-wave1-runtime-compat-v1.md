<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-wave1-runtime-compat-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-wave1-runtime-compat-v1
- Title: Local EXTRACT Wave 1 runtime compatibility
- Status: VALIDATING
- Capsule schema: v2

## Goal

Allow the already-authorized Local EXTRACT Wave 1 workload through the final privileged runtime workload gates without broadening gpu-heavy authority, then install the exact runtime fix and recover the existing benchmark request without issuing another trigger.

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

At the genuine root-control-plane boundary, install exact workspace-control merge 70d5668599de767647603ddec55815b9523d1bb8 through unchanged scripts/bootstrap_lambda_ci_p5.sh. Then resume ChatGPT/GitHub control and recover the existing Wave-1 execution without issuing another trigger.

## Remaining work

- Install exact runtime compatibility merge 70d5668599de767647603ddec55815b9523d1bb8 through unchanged root-owned P5 bootstrap.
- Verify manifest/policy/provisioner/controller identities remain accepted and all control-plane services are active.
- Resolve the terminal failed request state safely and recover the existing Wave-1 execution without another GitHub trigger.
- Follow run 39200075204/job 117891019967 through artifact and final root receipt.
- Return ownership upward after successful execution acceptance.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-runtime-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
