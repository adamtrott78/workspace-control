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

Stop at the authority gate. Obtain a reviewed authority path that either (A) promotes the validated PR #606 parent lineage through its owning task before this scientific candidate is promoted, or (B) explicitly authorizes a standalone main-based restage including architecture/lambda-ci-systemd-profiles.v1.json and scripts/install_padataset_scientific_runtime_v1.sh. After authority is durable, rebuild/restage from current main as required, exact-head validate again, then promote and reconcile. Do not move main, PR #606's head/base, or widen this capsule autonomously.

## Remaining work

- Contain the v3 control-small controller restart storm and recover after the GitHub REST primary-rate-limit window resets; preserve validation #466 without duplicate requests.
- Once #466 runs, require SUCCESS or diagnose its exact failure. Then recheck main and integrate current main into the activation branch with unchanged scientific tree, followed by exact-head validation of the integrated SHA.
- Advance the validated integrated policy to main so Lambda CI Project Reconcile installs the exact runtime/data/contract/route policy.
- Verify live reconciliation and run autonomous scientific smoke, bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation.
- Track the v3 controller 403 rate-limit handling defect for a separately authorized infrastructure hotfix; current code retries 429/5xx but treats primary-rate-limit 403 as fatal.

## Blockers / gates

- Promotion authority is blocked. PR #613 targets workspace-shell-multirepo-v3-reconcile-20261111 (PR #606 lineage), not main. Fast-forwarding main to edd1c378a1f9965299581dcb8210e5bb698a6717 would also promote the still-open parent reconciliation lineage and many paths outside this task's mutation authority.
- A standalone restage from main is also not currently authorized because the scientific task diff includes architecture/lambda-ci-systemd-profiles.v1.json and scripts/install_padataset_scientific_runtime_v1.sh, neither of which is listed in this task capsule's allowed_mutation_scope. Do not self-expand scope.
- Workspace Shell multirepo authority remains a separate owning-task concern; current Workspace Shell inspection for this PADataset task still fails TASK_NOT_FOUND in the trusted authority root.
- Scientific route must not be reconciled or invoked until an authority-correct promotion path is established and promoted policy is freshly reconciled.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
