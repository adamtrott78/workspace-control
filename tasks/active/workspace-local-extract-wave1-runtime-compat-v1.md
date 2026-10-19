<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-wave1-runtime-compat-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-wave1-runtime-compat-v1
- Title: Local EXTRACT Wave 1 runtime compatibility
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Allow the already-authorized Local EXTRACT Wave 1 workload through the final privileged runtime workload gates without broadening gpu-heavy authority, then install the exact runtime fix and recover the existing benchmark request without issuing another trigger.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: wave1-runtime-compat-v1
- Remote checkpoint: 246465494256ca7e2080c442c5a8e314e445c464
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Implement the minimal runtime compatibility patch on wave1-runtime-compat-v1: define/use an exact finite dual-GPU model-eval workload set containing model-eval-dual-gpu and model-eval-local-extract-wave1; include Wave 1 in promoted-model workloads; preserve generic gpu-heavy rejection; add focused regression tests.

## Remaining work

- Patch the three stale exact runtime workload gates and focused GPU runtime tests.
- Run Workspace Control validation and merge only after exact diff review.
- Install exact merged privileged runtime through unchanged P5 bootstrap.
- Resolve durable failed request state safely and recover existing Wave-1 run without another trigger.
- Return ownership upward after existing job executes or a new exact terminal blocker is identified.

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
