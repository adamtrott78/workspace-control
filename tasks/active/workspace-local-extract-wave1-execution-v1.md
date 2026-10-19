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
- Remote checkpoint: 6437ee9745468401f7c0d5daa40ea72e3be46257
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Do not issue another Wave-1 trigger. Complete bounded child workspace-local-extract-wave1-provisioner-compat-v1: update only the stale provisioner gpu-heavy workload guard and focused service tests to admit the already-live model-eval-local-extract-wave1 route alongside model-eval-dual-gpu, preserving generic gpu-heavy DENY. Validate/merge/install exact provisioner, then recover existing run 39200075204.

## Remaining work

- Complete workspace-local-extract-wave1-provisioner-compat-v1 and install the exact merged root provisioner; preserve accepted manifest/policy/model/runtime/GPU identities and generic gpu-heavy DENY.
- Recover the existing Wave-1 run 39200075204 / job 117891019967 without another trigger and follow it through artifact generation.
- Read the Wave-1 report artifact and final root-owned provisioner receipt; require exact model/runtime/two-GPU identity, non-scientific state, cleanup/postverify PASS, no residue/quarantine, then classify PROMISING/PARTIAL/REJECT.
- Checkpoint the result for parent research task research-engine-local-extract-redesign-v1 and archive support tasks after acceptance.

## Blockers / gates

- Root provisioner compatibility blocker: model-eval-local-extract-wave1 is live-authorized in manifest/policy and accepted by the fixed GPU controller, but scripts/lambda_ci_provisioner_service.py still rejects any gpu-heavy workload other than model-eval-dual-gpu. Existing run 39200075204 remains the sole authorized benchmark request.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
