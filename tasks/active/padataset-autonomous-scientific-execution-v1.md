<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

If this view disagrees with the JSON capsule or verified evidence, trust the capsule plus verified evidence.

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

Genuine root/operator authority gate: on the Lambda host, use exact validated head 52525fa00688cc80079f008a975131cee959402e and rerun the read-only Phase-A preflight. Only if every existing runner-class authority envelope is preserved may the operator create the exact root-owned 0600 EXPAND_PADATASET_SCIENTIFIC_V3_INACTIVE authorization receipt and invoke scripts/lambda_ci_v3_padataset_scientific_activation_v1.py --expand-inactive with --expected-head 52525fa00688cc80079f008a975131cee959402e. Do not run Phase B until the Phase-A committed receipt is verified.

## Remaining work

- On the Lambda host, use the exact validated correction head 52525fa00688cc80079f008a975131cee959402e to rerun the read-only Phase-A preflight; require exact preservation of every existing class root envelope, then create the root-owned one-shot EXPAND_PADATASET_SCIENTIFIC_V3_INACTIVE authority receipt.
- Run Phase A with scripts/lambda_ci_v3_padataset_scientific_activation_v1.py --expand-inactive; require the committed INSTALLED_INACTIVE transaction receipt, active ten-class shared provisioner, exact effective-generation verification, and proof that existing class controller InvocationID/MainPID/NRestarts values were preserved.
- Create/attest lambda-padataset-scientific-single-gpu with the already-reviewed v3 scale-set preflight; verify exact PADataset default-branch workflow blob, zero stale scientific runs, promoted runtime/base-Python integrity, and exact scientific-data identity.
- Create the separate root-owned ACTIVATE_PADATASET_SCIENTIFIC_V3 authority receipt and run Phase B; require only the scientific controller/route to become ACTIVE/ENABLED.
- Run scientific smoke, bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation with cleanup/runtime-integrity receipts.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated state is durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- Live Phase A now requires explicit root/operator authority on the Lambda host. GitHub repository authority cannot create the required root-owned 0600 one-shot authorization receipt or mutate /etc, /var/lib, systemd, or the shared provisioner.
- Live Workspace Shell trusted task authority still does not include padataset-autonomous-scientific-execution-v1, so privileged Workspace Shell helpers remain unavailable for this task.
- Phase B remains gated behind successful Phase A plus a fresh exact workflow/scale-set/runtime/data/no-stale-run preflight and a separate one-shot root/operator activation receipt.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
