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

Operator root runtime repair only: materialize exact workspace-control source b0f1c80b76e13e8333ab135a9d4cda437c3e3ce4, compute and bind the current installed runtime SHA, candidate runtime SHA, and existing runtime-override receipt SHA into one fresh root-owned 0600 REPAIR_PADATASET_SCIENTIFIC_RUNTIME_V1 authority, then invoke scripts/lambda_ci_v3_padataset_scientific_runtime_repair_v1.py. Require transaction phase COMMITTED_ACTIVE_RUNTIME_REPAIR, V3 installed-generation verification PASS, shared provisioner active/running, and restoration of exactly the previously active v3 controller set with unchanged UnitFileState/NRestarts. After repair, do not retrigger; observe existing run 43293735325 for the controller's terminal REST revival and fresh provision attempt.

## Remaining work

- Run the first live non-destructive scientific smoke through /lambda-scientific. It must verify exact workflow/runtime/data bindings, import torch, see exactly one authorized GPU, load the frozen Stage03 config, write only a tiny bounded artifact, and perform no training.
- After the non-destructive smoke passes and cleans up, run one bounded 1-epoch training smoke from an exact candidate PR with full cleanup/runtime-integrity receipts.
- Then execute the full frozen PA2 Stage03 backbone training, followed by Architecture C evaluation, preserving exact candidate/workflow/runtime/data provenance and bounded artifacts.
- Complete final cleanup/residue/runtime-integrity verification and durable task closure.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated scientific state and first live proofs are durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- The reviewed runtime repair is not yet installed on Lambda. Root/operator authority is required to execute scripts/lambda_ci_v3_padataset_scientific_runtime_repair_v1.py from exact workspace-control main b0f1c80b76e13e8333ab135a9d4cda437c3e3ce4.
- Do not issue another /lambda-scientific comment. Existing run 43293735325 / job 131446381843 must be allowed to revive through the controller's provenance-preserving terminal REST retry path after the runtime repair.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
