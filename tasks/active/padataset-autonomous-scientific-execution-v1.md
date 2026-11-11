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
- Remote checkpoint: c6341bbd195a0337d57e8cb4dde8d30b152aa3ff
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 100888178f362094c45807817f992d2653dcb7b2
- Remote verified: true

## Next safe action

Operator-only one-time bootstrap: from active DNNs, run scripts/install_padataset_scientific_runtime_v1.sh at exact validated workspace-control head 41a0d6ac0c00d81ebb12bbca24e21b838a62370e. Return PADATASET_DNNS_RUNTIME_BINDING_JSON, PADATASET_SCIENTIFIC_DATA_JSON, and PADATASET_SCIENTIFIC_PROMOTION=PASS.

## Remaining work

- Operator runs scripts/install_padataset_scientific_runtime_v1.sh once from exact validated source head and returns the final binding lines.
- ChatGPT commits exact DNNs runtime binding, activates the scientific contract/route, validates and reconciles live.
- ChatGPT creates an exact Stage03 experiment PR/request, triggers autonomous scientific smoke, then full PA2 Architecture C execution.
- ChatGPT inspects artifacts/receipts and continues scientific analysis without operator terminal work.

## Blockers / gates

- One-time operator/root promotion must run from exact validated source head 41a0d6ac0c00d81ebb12bbca24e21b838a62370e while the DNNs Conda environment is active.
- No routine scientific experiment can run until the emitted exact runtime/data bindings are committed, validated, activated, and reconciled.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
