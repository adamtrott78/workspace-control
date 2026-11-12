<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: padataset-autonomous-scientific-execution-v1
- Title: PADataset autonomous scientific execution v1
- Status: IN_PROGRESS
- Capsule schema: v2
- Current stage: scientific_activation_validation

## Goal

Make PADataset scientific GPU experiments autonomously executable by ChatGPT through the existing self-hosted Lambda control plane using an exact root-owned DNNs runtime, exact PR-head provenance, read-only project data/cache authority, bounded experiment request schemas, durable artifacts/receipts, and no per-run operator terminal work.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: padataset-autonomous-scientific-execution-v1
- Remote checkpoint: bb6528faf9643ffddf517891eba70f7988267d40
- Remote verified: false

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 100888178f362094c45807817f992d2653dcb7b2
- Remote verified: true

## Next safe action

Wait for the already-created exact-head validation #466 / run 43149651861 on bb6528faf9643ffddf517891eba70f7988267d40. If it succeeds, recheck main SHA before integrating; if it fails, diagnose the exact failing evidence. Do not submit a duplicate validation request or reconcile scientific policy while #466 remains queued.

## Remaining work

- Obtain SUCCESS for exact-head validation #466 on activation head bb6528faf9643ffddf517891eba70f7988267d40.
- Recheck current main. If main remains 3bee43a810d739cb199c5091024b8d91115aa5d6, move the activation branch to the prepared two-parent integration commit edd1c378a1f9965299581dcb8210e5bb698a6717; otherwise rebuild the integration against the new main. Then validate that exact integrated head.
- After integrated exact-head validation passes, advance reviewed policy to main so Lambda CI Project Reconcile validates it and the live reconcile controller installs the exact runtime/data/contract/route policy.
- Verify live reconciliation and then run the autonomous scientific smoke, bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation.

## Blockers / gates

- Dedicated exact-head Lambda CI Workspace Control Validation #466 / run 43149651861 is queued without runner assignment. Do not bypass this gate or create duplicate validation requests while it remains live.
- Scientific route must not be reconciled or invoked until the integrated main-compatible activation head passes exact-head validation and the live reconciler installs it.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
