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

Wait only for the already-issued authoritative Lambda CI Workspace Control Validation #484 / job 131520720719 on PR #622 exact head ae38809ce9b78facebe0565f254ef72c33112f19. If SUCCESS, merge PR #622, record the merge head, and prepare a fresh root-owned one-shot REFRESH_V3_CONTROLLER_BINARY_LIVE_V1 transaction bound to the exact currently installed controller SHA 01c5589c1fd38f2879f7c3688c7e45d2427079f5e7d061402768284164b29728, current controller-refresh receipt/source 78ae60364f472fd30654dd9018c90c546e3e8836, base manifest/root-policy identities, and freshly built reviewed candidate controller SHA. Execute the merged live repair only after proving no active provisioner hold/transient. After commit, do not retrigger scientific demand; monitor existing run 43293735325/job 131446381843 for terminal REST revival.

## Remaining work

- Run the first live non-destructive scientific smoke through /lambda-scientific. It must verify exact workflow/runtime/data bindings, import torch, see exactly one authorized GPU, load the frozen Stage03 config, write only a tiny bounded artifact, and perform no training.
- After the non-destructive smoke passes and cleans up, run one bounded 1-epoch training smoke from an exact candidate PR with full cleanup/runtime-integrity receipts.
- Then execute the full frozen PA2 Stage03 backbone training, followed by Architecture C evaluation, preserving exact candidate/workflow/runtime/data provenance and bounded artifacts.
- Complete final cleanup/residue/runtime-integrity verification and durable task closure.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated scientific state and first live proofs are durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- Authoritative self-hosted Validation #484 for PR #622 exact head ae38809ce9b78facebe0565f254ef72c33112f19 is queued. Do not merge or execute the live controller repair until it succeeds.
- Do not issue another /workspace-control-validate command, another /lambda-scientific comment, restart a controller, edit ledger state, or alter scale-set state.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
