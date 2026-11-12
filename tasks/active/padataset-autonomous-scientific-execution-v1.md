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

Operator recovery + fresh one-shot repair only. Materialize exact workspace-control main f7e0f72e82e20eef732ab78ebe082d91e4bd21dc. Read the latest scientific runtime-repair transaction receipt and require phase ROLLED_BACK_PREVIOUS_RUNTIME with rollback_completed=true; independently require installed runtime SHA 86a7c8e33d689b11ece5cd1456ff3af9e841ed6b62a84356e8727d9cd8e1b9da and runtime-override SHA d9548a56ab46e133aa321e804e310c0fad1712e87cda5cece56bda308fc5bcd0; verify installed generation and active scientific controller/provisioner. Then create a fresh root-owned 0600 REPAIR_PADATASET_SCIENTIFIC_RUNTIME_V1 authority bound to the current predecessor runtime/override and candidate runtime f2791ade8e951408d8a3818da617ec64919c06bd2f7d07c9f6fa0c137bb6afa2, invoke the corrected repair helper, and require COMMITTED_ACTIVE_RUNTIME_REPAIR. After success, do not retrigger; observe existing run 43293735325 / job 131446381843 for REST terminal-record revival.

## Remaining work

- Run the first live non-destructive scientific smoke through /lambda-scientific. It must verify exact workflow/runtime/data bindings, import torch, see exactly one authorized GPU, load the frozen Stage03 config, write only a tiny bounded artifact, and perform no training.
- After the non-destructive smoke passes and cleans up, run one bounded 1-epoch training smoke from an exact candidate PR with full cleanup/runtime-integrity receipts.
- Then execute the full frozen PA2 Stage03 backbone training, followed by Architecture C evaluation, preserving exact candidate/workflow/runtime/data provenance and bounded artifacts.
- Complete final cleanup/residue/runtime-integrity verification and durable task closure.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated scientific state and first live proofs are durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- Before retrying the root runtime repair, prove the failed attempt rolled back to the exact predecessor runtime SHA 86a7c8e33d689b11ece5cd1456ff3af9e841ed6b62a84356e8727d9cd8e1b9da and predecessor runtime-override SHA d9548a56ab46e133aa321e804e310c0fad1712e87cda5cece56bda308fc5bcd0, and inspect the failed transaction receipt phase. Do not reuse consumed authority d4f31151-331b-46e3-921b-e56ced421bfe.
- Do not issue another /lambda-scientific comment. Existing run 43293735325 / job 131446381843 remains the only scientific demand and must revive through the controller after a successful runtime repair.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
