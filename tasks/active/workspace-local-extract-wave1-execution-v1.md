<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-wave1-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-wave1-execution-v1
- Title: Trusted Lambda route for Local EXTRACT Wave 1
- Status: VALIDATING
- Capsule schema: v2

## Goal

Expose exactly the merged research-engine Local EXTRACT Wave 1 workflow to the already-accepted two-A4500 Qwen3.5 execution envelope, install that exact route on Lambda, execute one bounded nine-paper benchmark, and retire the route owner after final receipt/cleanup evidence. This task does not own EXTRACT scientific design or production routing.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d68c08d55a6f616667be3a7661fbd08ad54599d2
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Do not issue another Wave-1 trigger. Execute bounded child task workspace-local-extract-wave1-controller-compat-v1: patch only the GPU controller compatibility surfaces required for workload model-eval-local-extract-wave1 (workload selection, exact /lambda-ci-local-extract-wave1 command attestation, deterministic GPU runner identity), add fail-closed regression coverage preserving generic gpu-heavy DENY, validate/merge/install the exact controller, then recover existing run 39200075204 / job 117891019967.

## Remaining work

- Create and complete bounded child task workspace-local-extract-wave1-controller-compat-v1 to add only the missing controller workload/command/runner mappings plus regression tests; generic gpu-heavy must remain denied.
- Validate and merge the controller compatibility patch, install the exact merged root-owned controller through the accepted P5 deployment path, and verify controller health.
- Recover existing queued Wave 1 run 39200075204 / job 117891019967 after controller activation; do not post another trigger.
- Read the Wave-1 report artifact and final root-owned provisioner receipt; require exact model/runtime/two-GPU identity, non-scientific state, cleanup/postverify PASS, no residue/quarantine, then classify PROMISING/PARTIAL/REJECT.
- Checkpoint the execution result for parent research task research-engine-local-extract-redesign-v1 and archive this support task after acceptance.

## Blockers / gates

- Controller compatibility blocker: workspace-ci-controller-gpu is missing explicit model-eval-local-extract-wave1 handling in workload selection, command attestation, and deterministic GPU runner identity. Existing workflow run 39200075204 / job 117891019967 is queued and must be resumed after the bounded fix; do not retrigger.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
