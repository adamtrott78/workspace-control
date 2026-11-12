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

Operator live workflow-refresh gate: using exact reviewed workspace-control main 8208827862079b0a63719b427c76063d79358345, create a fresh root-owned 0600 workflow-refresh preflight proving PADataset main a7e3eb3718820f6fa3183ebc6b8990da2b49f61f, workflow blob 4cf390ec334b0569dbfc2399ff86c2d892f97586, zero active scientific workflow runs, scale-set id 5 assigned=0/running=0, and no local scientific ledger/provisioner/transient residue. Then create a separate one-shot REFRESH_PADATASET_SCIENTIFIC_WORKFLOW_V1 authority bound to the exact current scientific active receipt, preflight, old/new workflow blobs, current/new target controller-policy digests, and target class. Invoke scripts/lambda_ci_v3_padataset_scientific_workflow_refresh_v1.py. Require COMMITTED_ACTIVE_WORKFLOW_REFRESH, target controller active/running/enabled, shared provisioner preserved, and every non-target controller snapshot unchanged. Only after that commit, issue exactly one `/lambda-scientific 71ef2e5f72608737628164ed99be66e05d17e713 smoke` comment on PADataset PR #16.

## Remaining work

- Run the first live non-destructive scientific smoke through /lambda-scientific. It must verify exact workflow/runtime/data bindings, import torch, see exactly one authorized GPU, load the frozen Stage03 config, write only a tiny bounded artifact, and perform no training.
- After the non-destructive smoke passes and cleans up, run one bounded 1-epoch training smoke from an exact candidate PR with full cleanup/runtime-integrity receipts.
- Then execute the full frozen PA2 Stage03 backbone training, followed by Architecture C evaluation, preserving exact candidate/workflow/runtime/data provenance and bounded artifacts.
- Complete final cleanup/residue/runtime-integrity verification and durable task closure.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated scientific state and first live proofs are durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- The live scientific controller still trusts predecessor workflow blob e70412f3ccdc70826f56f7ba0255518f1f95224f while PADataset default branch now serves reviewed replacement blob 4cf390ec334b0569dbfc2399ff86c2d892f97586; admission therefore remains intentionally fail-closed until the one-shot root workflow-refresh transaction commits.
- Live Workspace Shell trusted task authority still does not include padataset-autonomous-scientific-execution-v1, so the root-owned live workflow refresh requires the operator to invoke the reviewed helper with sudo.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
