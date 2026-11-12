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
- Remote checkpoint: edd1c378a1f9965299581dcb8210e5bb698a6717
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 100888178f362094c45807817f992d2653dcb7b2
- Remote verified: true

## Next safe action

Use this exact authority-state head as /etc/workspace-shell/authority input to the already-validated multirepo upgrade operator, with workspace-control execution SHA 1a9a24fc1bc6e5cda2984e296151a378138600c8 and PADataset execution SHA 17e1147614f27702e43565089d618182ff71c5af. After LOCAL_TASK_AUTHORITY=PASS, verify live Workspace Shell visibility for workspace-shell-multirepo-research-v1, mth602-final-multisurrogate-dqnguard-v1, and padataset-autonomous-scientific-execution-v1. Then restage only the scientific changes from current main under the now-explicitly-authorized scope and exact-head validate again.

## Remaining work

- Contain the v3 control-small controller restart storm and recover after the GitHub REST primary-rate-limit window resets; preserve validation #466 without duplicate requests.
- Once #466 runs, require SUCCESS or diagnose its exact failure. Then recheck main and integrate current main into the activation branch with unchanged scientific tree, followed by exact-head validation of the integrated SHA.
- Advance the validated integrated policy to main so Lambda CI Project Reconcile installs the exact runtime/data/contract/route policy.
- Verify live reconciliation and run autonomous scientific smoke, bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation.
- Track the v3 controller 403 rate-limit handling defect for a separately authorized infrastructure hotfix; current code retries 429/5xx but treats primary-rate-limit 403 as fatal.

## Blockers / gates

- Live Workspace Shell trusted authority is stale and must be refreshed before using Workspace Shell for the scientific task. The validated multirepo upgrade operator is the authorized host-mutation path.
- Scientific promotion must still be restaged cleanly from current main after Workspace Shell authority refresh; do not merge the stacked PR #606 lineage into main.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
