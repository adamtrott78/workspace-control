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
- Remote checkpoint: 611cbdb5a89c6da0db6b4b98ac3f3faac7d5b7ca
- Remote verified: false

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 100888178f362094c45807817f992d2653dcb7b2
- Remote verified: true

## Next safe action

Exact-head validate the clean main-based PR head. If PASS, mark the clean implementation verified, promote it to main through the reviewed PR path, let the production reconciler activate the scientific policy, then refresh Workspace Shell trusted authority once to the final promoted task state before scientific execution.

## Remaining work

- Contain the v3 control-small controller restart storm and recover after the GitHub REST primary-rate-limit window resets; preserve validation #466 without duplicate requests.
- Once #466 runs, require SUCCESS or diagnose its exact failure. Then recheck main and integrate current main into the activation branch with unchanged scientific tree, followed by exact-head validation of the integrated SHA.
- Advance the validated integrated policy to main so Lambda CI Project Reconcile installs the exact runtime/data/contract/route policy.
- Verify live reconciliation and run autonomous scientific smoke, bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation.
- Track the v3 controller 403 rate-limit handling defect for a separately authorized infrastructure hotfix; current code retries 429/5xx but treats primary-rate-limit 403 as fatal.

## Blockers / gates

- Clean main-based scientific restage is prepared and must pass exact-head validation before promotion.
- Live Workspace Shell trusted authority still does not include padataset-autonomous-scientific-execution-v1; refresh that authority only after the final clean candidate SHA is validated and bound.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
