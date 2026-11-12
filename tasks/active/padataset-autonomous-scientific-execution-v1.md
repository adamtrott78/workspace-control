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

## Goal

Make PADataset scientific GPU experiments autonomously executable by ChatGPT through the existing self-hosted Lambda control plane using an exact root-owned DNNs runtime, exact PR-head provenance, read-only project data/cache authority, bounded experiment request schemas, durable artifacts/receipts, and no per-run operator terminal work.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: padataset-autonomous-scientific-execution-v1
- Remote checkpoint: 52525fa00688cc80079f008a975131cee959402e
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d27eb8feb481696548766b8df325737d766a8d3a
- Remote verified: true

## Next safe action

Operator bootstrap controller repair from exact PR #622 head ae38809ce9b78facebe0565f254ef72c33112f19 only. Do not merge PR #622 first. Build the exact controller with pinned Go 1.26.3, bind current installed controller SHA, active controller-refresh receipt SHA/source, base manifest SHA/source, and current root-policy SHA into a fresh root-owned 0600 REFRESH_V3_CONTROLLER_BINARY_LIVE_V1 authority, invoke scripts/lambda_ci_v3_live_controller_repair_v1.py, and require COMMITTED_ACTIVE_CONTROLLER_REPAIR plus installed-generation verification. Then observe existing authoritative Validation #484/job 131520720719; if it succeeds, merge PR #622. If the repair fails, use its transaction receipt/rollback evidence and do not retry blindly.

## Remaining work

- Run the first live non-destructive scientific smoke through /lambda-scientific. It must verify exact workflow/runtime/data bindings, import torch, see exactly one authorized GPU, load the frozen Stage03 config, write only a tiny bounded artifact, and perform no training.
- After the non-destructive smoke passes and cleans up, run one bounded 1-epoch training smoke from an exact candidate PR with full cleanup/runtime-integrity receipts.
- Then execute the full frozen PA2 Stage03 backbone training, followed by Architecture C evaluation, preserving exact candidate/workflow/runtime/data provenance and bounded artifacts.
- Complete final cleanup/residue/runtime-integrity verification and durable task closure.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated scientific state and first live proofs are durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- Authoritative Validation #484 cannot run until the stale shared v3 controller binary is replaced, but PR #622 must not be merged before #484 succeeds. This is a bootstrap dependency loop.
- The only safe forward path is an operator-authorized one-shot transactional install of exact PR #622 head ae38809ce9b78facebe0565f254ef72c33112f19 while PR #622 remains open, with pre-swap quiescence and rollback. After install, existing #484 must run and pass before PR #622 is merged.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
