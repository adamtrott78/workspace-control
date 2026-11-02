<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-control-plane-protocol-redesign-v1
- Title: GitHub Actions Control-Plane Protocol Redesign v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Replace the current parser-chained GitHub Actions runner admission path with a formally modeled, versioned, typed control-plane protocol whose routing, authority, scheduling, provisioning, execution, recovery, and lifecycle semantics are explicit end-to-end, so any executor request admitted by policy cannot later be falsely rejected by a downstream parser that implements a different grammar.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 78ae60364f472fd30654dd9018c90c546e3e8836
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 6165556086b73d2076f205f11ec7b988150f23dd
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: a8f952c7cf964730a01b2dc5c6cd75850912f94f
- Remote verified: true

## Next safe action

Validate the bounded legacy retirement tool at the exact branch head, then execute retirement only for the three production-accepted legacy scale sets: lambda-workspace-control, lambda-padataset, and lambda-padataset-gpu. Require the committed production transaction /var/lib/workspace-ci/v3/migration/358b3fb9-f702-401e-b6bd-69d8c89f3488/transaction.json, all six GitHub scale-set statistics at zero for each retiring set, accepted target v3 scale-set presence, all v2 controllers inactive+disabled, accepted v3 controllers active+enabled, and a root-owned rollback-window receipt persisted before any deletion. Preserve lambda-research-engine and lambda-research-engine-gpu because their replacement v3 classes are not accepted; preserve all v2 bytes/config/state. After the three accepted legacy scale sets are retired and independently verified absent, resume workspace-semantic-execution-migration-v1.

## Remaining work

- Validate the exact-head bounded retirement implementation.
- Retire only lambda-workspace-control, lambda-padataset, and lambda-padataset-gpu after all migration-plan per-scale-set preconditions pass.
- Preserve lambda-research-engine and lambda-research-engine-gpu until their replacement v3 classes receive separate acceptance.
- Preserve all v2 installed bytes/config/state through the rollback window; do not remove legacy controller config/state during scale-set retirement.
- Record the root-owned rollback-window/retirement receipt and independently verify the three accepted legacy scale sets are absent.
- Immediately resume workspace-semantic-execution-migration-v1 umbrella work after accepted scale-set retirement.

## Blockers / gates

- The three production-accepted legacy scale sets have not yet been physically retired.
- Research legacy scale sets are explicitly not eligible for deletion because their replacement v3 classes are not accepted/active.
- Legacy controller bytes/config/state must remain preserved through the rollback window and are not authorized for deletion in this transition.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
