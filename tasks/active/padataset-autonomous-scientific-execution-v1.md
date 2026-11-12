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

Perform read-only operator diagnosis only; do NOT create another /lambda-scientific comment. Inspect workspace-ci-v3-controller@padataset-scientific-single-gpu-v1.service state and recent journal, rerun the reviewed v3-canary-preflight against scale-set lambda-padataset-scientific-single-gpu to capture assigned/running counts, inspect only the target scientific controller ledger and target-class provisioner records/transients, and correlate with queued GitHub run 43293735325 / job 131446381843. If controller is healthy and scale-set assigned=1 but no local admission, diagnose verifier/message-session path. If controller exited, diagnose exact journal failure before any restart. If capacity is held by another class, wait/resolve that class without duplicating scientific demand. Only resume the existing smoke after the cause is proven.

## Remaining work

- Run the first live non-destructive scientific smoke through /lambda-scientific. It must verify exact workflow/runtime/data bindings, import torch, see exactly one authorized GPU, load the frozen Stage03 config, write only a tiny bounded artifact, and perform no training.
- After the non-destructive smoke passes and cleans up, run one bounded 1-epoch training smoke from an exact candidate PR with full cleanup/runtime-integrity receipts.
- Then execute the full frozen PA2 Stage03 backbone training, followed by Architecture C evaluation, preserving exact candidate/workflow/runtime/data provenance and bounded artifacts.
- Complete final cleanup/residue/runtime-integrity verification and durable task closure.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated scientific state and first live proofs are durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- Scientific workflow run 43293735325 is queued with no scheduler transition. Before any retrigger or training, read-only live diagnosis must determine whether the dedicated scientific controller is still active, whether scale-set 5 now reports assigned=1/running=0, and whether controller journal/ledger shows admission rejection, message-session failure, or capacity wait.
- Live Workspace Shell trusted authority still does not include padataset-autonomous-scientific-execution-v1, so connected Workspace Shell cannot inspect this live controller without an explicit authority/trust change; do not widen trust merely to diagnose this run.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
