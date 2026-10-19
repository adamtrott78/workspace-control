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
- Remote checkpoint: 7544190ff9e87e7defcd1148550e57a637a19e34
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Do not issue another Wave-1 trigger. Read durable state/receipt for accepted request fd30c4c6-6756-55d1-a12d-e3cb16f50d20; GitHub run 39200075204/job 117891019967 remains queued with no assigned runner.

## Remaining work

- Read durable root provisioner state and runtime receipt for request fd30c4c6-6756-55d1-a12d-e3cb16f50d20.
- Follow existing run 39200075204/job 117891019967 after worker state is resolved; do not trigger a second run.
- Read Wave-1 report artifact and final root receipt; require exact model/runtime/two-GPU identity, non-scientific state, cleanup/postverify PASS, no residue/quarantine, then classify PROMISING/PARTIAL/REJECT.
- Checkpoint the result into research-engine-local-extract-redesign-v1 and archive support tasks.

## Blockers / gates

- Post-acceptance worker state unresolved: root provisioner accepted the sole authorized Wave-1 request, but GitHub still shows job 117891019967 queued/no runner. Durable request state/receipt is required before any further execution decision.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
