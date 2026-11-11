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
- Remote checkpoint: 7692508a1daa0ff4278bd08042388c2fa4f9c2cb
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: autonomous-scientific-execution-v1
- Remote checkpoint: 8dc3a087fbad932ac1a17df7ef963b18affc4c8f
- Remote verified: true

## Next safe action

Open validation PRs for the exact implementation candidates. Keep scientific route/contract planned and fail-closed until validation, workflow merge, and one-time DNNs/data promotion complete.

## Remaining work

- Pass workspace-control exact-head validation for planned scientific authority and installer.
- Validate and merge the trusted PADataset scientific workflow to default main without activating the route.
- Run the one-time validated DNNs/cache promoter and capture exact runtime/data bindings.
- Bind exact runtime and trusted workflow blob, activate the scientific contract/route, validate, reconcile live.
- Run autonomous scientific smoke, then full Stage 03 PA2 Architecture C experiment.

## Blockers / gates

- Implementation requires exact-head repository validation before DNNs promotion or live activation.
- PADataset trusted workflow must be merged to default main and exact blob-bound before route activation.
- DNNs/runtime + Stage03 cache promotion is a one-time operator/root action after installer validation; routine scientific runs require no operator action.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
