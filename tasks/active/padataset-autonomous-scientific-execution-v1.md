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

First live proof only: issue exactly one non-destructive /lambda-scientific smoke request through the trusted PADataset workflow, bound to the current exact scientific workflow blob e70412f3ccdc70826f56f7ba0255518f1f95224f, runtime padataset-dnns-v1, runtime tree 6922847a7ea87c318a36e1fd2cd3af5283e768ff06de90c4cb2558ea0d48cdaa, data profile ota_core_high_run01_len16384_v1 digest a76730a886909f9896e7cb7e9d1aede3d2301240f9ce08a4080e24d637406bf5, scale-set id 5, and exact candidate PR head. The smoke must import torch, verify exactly one authorized GPU, load the frozen Stage03 config, write only a tiny bounded artifact, perform no training, and end with zero assigned/running jobs, no transient residue, and runtime-integrity PASS before any training smoke is authorized.

## Remaining work

- Run the first live non-destructive scientific smoke through /lambda-scientific. It must verify exact workflow/runtime/data bindings, import torch, see exactly one authorized GPU, load the frozen Stage03 config, write only a tiny bounded artifact, and perform no training.
- After the non-destructive smoke passes and cleans up, run one bounded 1-epoch training smoke from an exact candidate PR with full cleanup/runtime-integrity receipts.
- Then execute the full frozen PA2 Stage03 backbone training, followed by Architecture C evaluation, preserving exact candidate/workflow/runtime/data provenance and bounded artifacts.
- Complete final cleanup/residue/runtime-integrity verification and durable task closure.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated scientific state and first live proofs are durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- No activation blocker remains: the dedicated scientific class/route are live. The next safety gate is the non-destructive first-live scientific smoke; do not jump directly to training.
- Live Workspace Shell trusted task authority still does not include padataset-autonomous-scientific-execution-v1, so privileged Workspace Shell helpers remain unavailable for this task until a later explicit authority refresh.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
