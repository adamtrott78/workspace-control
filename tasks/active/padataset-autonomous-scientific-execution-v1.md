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

Read-only controller-binary provenance gate only. On Lambda, read /etc/workspace-ci/v3/install-manifest.json source_head and controller entry digest; hash /opt/workspace-ci/v3/controller/lambda-ci-controller-v3; read /var/lib/workspace-ci/v3/controller-refresh/active.json if present; then reproducibly build controller/lambda-ci-controller/v3 from exact reviewed source 59ca152a497300e2f8854145860c7bb4313ff739 using pinned Go 1.26.3 -mod=readonly -trimpath and compare its SHA-256 to the installed binary. If the installed binary does not match either the base manifest or an active controller-refresh receipt/source build, fail closed. If it matches an older valid override whose source predates the required revival behavior, implement a transactional live controller-binary refresh that quiesces the currently-active controller set, preserves root services and controller topology, and then allows the existing queued scientific job to revive without retrigger.

## Remaining work

- Run the first live non-destructive scientific smoke through /lambda-scientific. It must verify exact workflow/runtime/data bindings, import torch, see exactly one authorized GPU, load the frozen Stage03 config, write only a tiny bounded artifact, and perform no training.
- After the non-destructive smoke passes and cleans up, run one bounded 1-epoch training smoke from an exact candidate PR with full cleanup/runtime-integrity receipts.
- Then execute the full frozen PA2 Stage03 backbone training, followed by Architecture C evaluation, preserving exact candidate/workflow/runtime/data provenance and bounded artifacts.
- Complete final cleanup/residue/runtime-integrity verification and durable task closure.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated scientific state and first live proofs are durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- Need read-only proof of the installed v3 controller binary provenance: base install-manifest source_head/controller digest, active controller-refresh receipt if present, actual installed controller SHA-256, and SHA-256 of a fresh Go 1.26.3 build from reviewed source 59ca152a497300e2f8854145860c7bb4313ff739. Do not refresh controller binary until this mismatch is proven.
- Do not issue another /lambda-scientific comment, restart the scientific controller, edit its ledger, or mutate scale-set state. Existing run 43293735325/job 131446381843 remains the sole demand.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
