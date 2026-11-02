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

Design, validate, and execute only the bounded legacy v2 scale-set retirement transition permitted by `architecture/lambda-ci-v3-migration-plan.v1.json#legacy_retirement`. Preconditions must include the accepted production transaction `/var/lib/workspace-ci/v3/migration/358b3fb9-f702-401e-b6bd-69d8c89f3488/transaction.json` in committed state, zero queued/assigned/running legacy jobs, no active runner registrations owned by legacy prefixes, accepted v3 route/class proof, and a recorded rollback-window receipt. Preserve all old installed v2 bytes/config/state through the rollback window; do not remove legacy controller config/state in this transition. After scale-set retirement is accepted, resume `workspace-semantic-execution-migration-v1` immediately; physical controller config/state deletion is a later cleanup task.

## Remaining work

- Validate and execute bounded retirement of the five legacy v2 scale sets only after proving the migration-plan `legacy_retirement` preconditions.
- Preserve old v2 installed bytes/config/state through the rollback window; do not remove legacy controller config/state during scale-set retirement.
- Record exact legacy scale-set retirement evidence and keep Research GPU containment provenance intact.
- Immediately resume `workspace-semantic-execution-migration-v1` umbrella work after legacy scale-set retirement acceptance.
- Perform physical legacy controller config/state deletion only in a later separately validated cleanup task.

## Blockers / gates

- Legacy physical scale-set retirement has not yet been executed; migration policy requires zero queued/assigned/running jobs, no active legacy runner registrations, accepted v3 route/class proof, and a recorded rollback-window receipt.
- Legacy controller bytes/config/state must remain preserved through the rollback window and are not authorized for deletion in the scale-set retirement transition.
- Research GPU containment provenance must remain intact; no Research v3 route activation is implied by production cutover acceptance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
