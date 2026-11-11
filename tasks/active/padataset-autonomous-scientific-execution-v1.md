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

Validate the exact pre-promotion policy snapshot with workflow blob 555c2bd1f824519281f149017898d4923439d6cc bound. Route remains PLANNED_NOT_BOUND and scientific contract remains PLANNED_NOT_ACCEPTED.

## Remaining work

- Pass exact-head validation with trusted scientific workflow blob bound while route remains planned.
- Run the one-time validated DNNs/cache promoter and capture exact runtime/data bindings.
- Commit exact runtime binding, activate scientific contract/route, validate and reconcile live.
- Run autonomous scientific smoke, then full Stage 03 PA2 Architecture C experiment.

## Blockers / gates

- Final pre-promotion workspace-control validation must pass after binding the exact default-branch scientific workflow blob.
- DNNs/runtime + Stage03 cache promotion is a one-time operator/root action; route and contract remain planned/fail-closed until exact promotion bindings are captured.
- After promotion, exact runtime binding must be committed and validated before activation/reconciliation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
