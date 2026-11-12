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
- Remote checkpoint: 46f6b048b93014d24254be232bb3e17f8e0a900d
- Remote verified: false

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d27eb8feb481696548766b8df325737d766a8d3a
- Remote verified: true

## Next safe action

Implement and regression-cover the two-phase additive scientific v3 activation transaction and effective-generation verifier on branch padataset-autonomous-scientific-execution-v1, based on promoted main dff9024e16f36767facd3cbbbf1009f62b9899f7. Do not mutate live host state. After implementation, obtain normal and authoritative exact-head repository validation before any live Phase A/Phase B execution.

## Remaining work

- Implement the repository-only two-phase additive scientific v3 activation transaction plus effective-generation verifier support and regression tests within existing task authority.
- Open a fresh Workspace Control PR for that activation implementation; require normal Workspace Control Validation PASS, then exactly one authoritative /workspace-control-validate request and PASS on the identical frozen SHA before merge.
- After the reviewed activation implementation is promoted, execute Phase A expansion on the live host only through explicit operator/root authority: prove quiescent shared provisioner state, install the ten-class effective generation with the scientific class INSTALLED/INACTIVE and route DISABLED, restart only the shared provisioner, and prove existing class controllers were not restarted.
- Execute Phase B only after exact workflow/runtime/data/no-stale-run and target scale-set preflights; activate only the scientific controller/route and verify dedicated identity/bindings.
- Run scientific smoke, bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation with cleanup/runtime-integrity receipts.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 only after the final promoted/activated state is durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- The additive scientific v3 activation transaction/verifier is designed but not yet implemented or exact-head validated.
- No live host activation has been attempted for padataset-scientific-single-gpu-v1; live scientific admission remains unavailable.
- Live Workspace Shell trusted task authority still does not include padataset-autonomous-scientific-execution-v1; do not use privileged Workspace Shell helpers for this task before final activation state is durable.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
