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
- Remote checkpoint: 958d6f8ed0989b2846d04b3bd3eb2ace41f5372c
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

At the root HUMAN_TERMINAL boundary, install exact runtime merge 70d5668599de767647603ddec55815b9523d1bb8. Then, only if request fd30c4c6-6756-55d1-a12d-e3cb16f50d20 still exactly matches the proven prelaunch FAILED state and still has zero execution material/residue/quarantine, archive that state with SHA256, remove only its active state file, restart workspace-ci-controller-gpu.service, and let the same GitHub job recover. Do not trigger another run.

## Remaining work

- Install exact runtime compatibility merge 70d5668599de767647603ddec55815b9523d1bb8 through unchanged P5 bootstrap.
- Before re-arm, re-prove the exact FAILED state/error and absence of receipt/log/unit/process/GPU/quarantine execution evidence.
- Archive the root-owned failed state with SHA256 under /var/lib/workspace-ci/provisioner/recovery-evidence and remove only the active state file for fd30c4c6-6756-55d1-a12d-e3cb16f50d20.
- Restart only workspace-ci-controller-gpu.service and allow JobAssigned recovery to reconcile orphan JIT state and regenerate the same deterministic request; do not post another trigger.
- Resume ChatGPT/GitHub following of run 39200075204/job 117891019967 and validate runtime/artifact/final receipt.

## Blockers / gates

- Genuine root-control-plane operation required: install exact runtime merge 70d5668599de767647603ddec55815b9523d1bb8, then perform the narrowly authorized prelaunch re-arm of request fd30c4c6-6756-55d1-a12d-e3cb16f50d20 by archiving the exact FAILED state and clearing only its active state file before restarting the GPU controller.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-runtime-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
