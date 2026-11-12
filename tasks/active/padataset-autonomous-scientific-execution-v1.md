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

Follow exact integration validation #467 / run 43229075867 to terminal state. If SUCCESS, verify main and PR/base authority remain unchanged, then resolve the reviewed promotion path to main without relying on PR #613's current non-main base. Do not create another validation run.

## Remaining work

- Contain the v3 control-small controller restart storm and recover after the GitHub REST primary-rate-limit window resets; preserve validation #466 without duplicate requests.
- Once #466 runs, require SUCCESS or diagnose its exact failure. Then recheck main and integrate current main into the activation branch with unchanged scientific tree, followed by exact-head validation of the integrated SHA.
- Advance the validated integrated policy to main so Lambda CI Project Reconcile installs the exact runtime/data/contract/route policy.
- Verify live reconciliation and run autonomous scientific smoke, bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation.
- Track the v3 controller 403 rate-limit handling defect for a separately authorized infrastructure hotfix; current code retries 429/5xx but treats primary-rate-limit 403 as fatal.

## Blockers / gates

- Exact integration validation #467 / run 43229075867 for edd1c378a1f9965299581dcb8210e5bb698a6717 is queued. Do not duplicate or cancel it.
- PR #613 currently targets workspace-shell-multirepo-v3-reconcile-20261111 rather than main; do not treat PR merge as main promotion without separately resolving the intended authority/base path.
- Scientific route must not be reconciled or invoked until the integrated exact-head validation succeeds and the reviewed policy is promoted/reconciled through the authorized path.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
