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
- Remote checkpoint: f627c113de479258c45cd32c4ba146139481ea5d
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 100888178f362094c45807817f992d2653dcb7b2
- Remote verified: true

## Next safe action

Execute the one-time validated Python-venv promotion from exact capability head f627c113de479258c45cd32c4ba146139481ea5d on the Lambda host using operator sudo/private-source authority. Capture the emitted runtime/data binding JSON and promotion PASS line. Do not activate the scientific route until those exact bindings are returned and committed.

## Remaining work

- Run the one-time root/private-source promotion from exact validated capability head f627c113de479258c45cd32c4ba146139481ea5d and capture PADATASET_DNNS_RUNTIME_BINDING_JSON, PADATASET_SCIENTIFIC_DATA_JSON, and PADATASET_SCIENTIFIC_PROMOTION=PASS.
- After successful promotion, commit the exact DNNs runtime/data bindings, activate scientific-single-gpu-v1 and the PADataset scientific route, validate the exact activation head, and reconcile live control-plane state.
- Run the autonomous scientific smoke and bounded training smoke, then create the exact Stage03 request, train the frozen PA2 four-known-class backbone, run Architecture C evaluation, validate result_record.json, and inspect artifacts/receipts.

## Blockers / gates

- The corrected promoter is exact-head validated at f627c113de479258c45cd32c4ba146139481ea5d, but the one-time root/private-source promotion has not yet been executed. This remains an operator-only authority gate because it requires sudo and reads the private DNNs source/cache under /home/atrott.
- Routine scientific execution remains disabled until the validated promoter emits exact runtime/data bindings, those bindings are committed, the scientific contract/route is activated and validated, and live reconciliation succeeds.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
