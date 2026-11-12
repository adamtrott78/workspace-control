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

Create a fresh root-owned 0600 one-shot ACTIVATE_PADATASET_SCIENTIFIC_V3 authority receipt bound to exact source head 52525fa00688cc80079f008a975131cee959402e, scientific inactive active-receipt SHA-256 610135349dcb37404b90473bc5d1b7eaf9d58a196c60d65e61a40c52467512b7, preflight confirmation SHA-256 1aacf7b39ada250653759499894a9e20e97e1d10423024fc32c0f1d844a6023f, target class/route/scale-set, trusted workflow blob, runtime manifest identity, and scientific-data digest; then invoke scripts/lambda_ci_v3_padataset_scientific_activation_v1.py --activate with the exact preflight confirmation. Require COMMITTED_ACTIVE, target controller active/running/enabled, route ENABLED, and all existing controller snapshots preserved.

## Remaining work

- Run the fresh Phase-B activation preflight: verify effective generation is still INSTALLED/INACTIVE with route DISABLED; re-attest promoted runtime tree/base-Python and scientific-data digests; verify exact PADataset default-branch scientific workflow blob and zero queued/in-progress scientific workflow runs; create/attest lambda-padataset-scientific-single-gpu with the reviewed v3 scale-set preflight and require zero assigned/running jobs; verify the PADataset controller credential remains project-scoped.
- Create the separate root-owned ACTIVATE_PADATASET_SCIENTIFIC_V3 authority receipt bound to the exact inactive-generation receipt, fresh preflight confirmation, scale-set identity, workflow blob, runtime/data identities, target class/route, then run Phase B; require only the scientific controller/route to become ACTIVE/ENABLED while all existing controller snapshots remain unchanged.
- Run the non-destructive scientific smoke, then one bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation with cleanup/runtime-integrity receipts.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated state is durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- Phase B requires a fresh operator/root-owned activation preflight confirmation and separate one-shot ACTIVATE_PADATASET_SCIENTIFIC_V3 authority receipt; Phase-A authority cannot be reused.
- Live Workspace Shell trusted task authority still does not include padataset-autonomous-scientific-execution-v1, so privileged Workspace Shell helpers remain unavailable for this task.
- Scientific execution remains admission-disabled until the full Phase-B preflight and activation transaction commit.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
