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
- Remote checkpoint: d69c5c3f3af5619c72a0a11c437a8edead4a8022
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 100888178f362094c45807817f992d2653dcb7b2
- Remote verified: true

## Next safe action

Operator-only one-time bootstrap: from the active DNNs shell, run scripts/install_padataset_scientific_runtime_v1.sh at exact validated workspace-control head d69c5c3f3af5619c72a0a11c437a8edead4a8022. Return the final PADATASET_DNNS_RUNTIME_BINDING_JSON, PADATASET_SCIENTIFIC_DATA_JSON, and PADATASET_SCIENTIFIC_PROMOTION=PASS lines.

## Remaining work

- Operator runs scripts/install_padataset_scientific_runtime_v1.sh once from exact validated source head and returns the final binding lines.
- ChatGPT commits exact DNNs runtime binding, activates the scientific contract/route, validates and reconciles live.
- ChatGPT creates an exact Stage03 experiment PR/request, triggers autonomous scientific smoke, then full PA2 Architecture C execution.
- ChatGPT inspects artifacts/receipts and continues scientific analysis without operator terminal work.

## Blockers / gates

- One-time operator/root promotion must run from exact validated source head d69c5c3f3af5619c72a0a11c437a8edead4a8022 while the DNNs Conda environment is active.
- No routine scientific experiment can run until the emitted exact runtime/data bindings are committed, validated, activated, and reconciled.
