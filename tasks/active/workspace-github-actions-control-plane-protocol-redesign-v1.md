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
- Remote checkpoint: d5d3337a17c8ea3c0a62e9909b1a03cd11da7220
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 94edb809f4c295902911f8cc4b3652a9121ac715
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 35e6f451fe36f039b5f6461f7469f0eed1e79e43
- Remote verified: true

## Next safe action

Continue producer_and_policy_compiler_design on PR #572: freeze projection/deployment schemas and implement a repository-only compiler prototype that generates root/controller/executor projections and the 23-route compatibility matrix. Do not mutate Lambda, restart controllers, apply PR #571, or retrigger host-attest.

## Remaining work

- Finish producer/policy compiler design: exact projection schemas, catalog-generation digest algorithm, deployment-overlay schema, and class-specific systemd/controller identity projection.
- Design the executor builder interface so every execution/maintenance trigger is selected by action_id and typed arguments rather than raw comment text.
- Define legacy-to-v3 migration overlay preserving current workspace-control containment and research-engine GPU quarantine/retry-invalidated authority without implicit route activation.
- Implement repository-only compiler/projection prototype and compatibility matrix for all 23 routes and nine runner classes.
- Implement deterministic/state-machine/fault-injection verification plan; do not modify live Lambda.
- Only after repository-only verification passes, design a separately authorized one-class-at-a-time migration and live acceptance.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
