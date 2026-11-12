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

Prepare a corrected operator bootstrap for exact still-open PR #622 head ae38809ce9b78facebe0565f254ef72c33112f19. Before creating fresh authority, re-prove installed controller SHA 01c5589c1fd38f2879f7c3688c7e45d2427079f5e7d061402768284164b29728, ACTIVE predecessor controller-refresh source 78ae60364f472fd30654dd9018c90c546e3e8836, effective-generation PASS, no live provisioner hold/transient, and candidate controller SHA 7367021d8d84cff9a5e7eab64d95ef50d23135b8790574b1b2ab9b03ec6574b2. Create a NEW root-owned 0600 REFRESH_V3_CONTROLLER_BINARY_LIVE_V1 authority whose root_policy_sha256 value is manifest['root_policy_sha256'] from /etc/workspace-ci/v3/install-manifest.json, exactly matching scripts/lambda_ci_v3_live_controller_repair_v1.py. Invoke the exact PR #622 helper once. Require COMMITTED_ACTIVE_CONTROLLER_REPAIR and generation verification. Then do not retrigger anything: allow existing authoritative Validation #484 to run on exact PR #622 head; only after #484 succeeds may PR #622 be merged. Existing PADataset smoke run 43293735325/job 131446381843 remains the sole scientific demand.

## Remaining work

- Run the first live non-destructive scientific smoke through /lambda-scientific. It must verify exact workflow/runtime/data bindings, import torch, see exactly one authorized GPU, load the frozen Stage03 config, write only a tiny bounded artifact, and perform no training.
- After the non-destructive smoke passes and cleans up, run one bounded 1-epoch training smoke from an exact candidate PR with full cleanup/runtime-integrity receipts.
- Then execute the full frozen PA2 Stage03 backbone training, followed by Architecture C evaluation, preserving exact candidate/workflow/runtime/data provenance and bounded artifacts.
- Complete final cleanup/residue/runtime-integrity verification and durable task closure.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated scientific state and first live proofs are durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- PR #622 authoritative Validation #484 / job 131520720719 remains queued because the stale live shared controller creates the self-validation bootstrap loop; PR #622 remains open and unmerged.
- The first operator bootstrap authority d2d5fdd6-5605-4a5e-8f44-be0f437fe2a4 is invalid for the reviewed helper and must never be reused. It failed before authority consumption/live mutation.
- A corrected bootstrap must bind root_policy_sha256 to the base install manifest's `root_policy_sha256` field exactly, not SHA-256 of the current root-policy.json file.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
