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
- Remote checkpoint: 2281b005dca2ceee955eabeb2d0e7c888ab23a0b
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

Continue repository_only_protocol_verification on PR #572: implement pure controller/capacity state-machine prototypes and fault-injection tests for all scheduler/recovery boundaries. Do not mutate Lambda, restart controllers, apply PR #571, or retrigger host-attest.

## Remaining work

- Implement repository-only runner-class controller admission/supervisor state-machine model against the exact pinned actions/scaleset lifecycle semantics.
- Implement repository-only two-phase root capacity/resource allocator model: RESERVE, LAUNCH, STATUS, CANCEL, crash reconciliation and class quarantine.
- Implement fault-injection/model tests for redelivery, reassignment, TotalAssignedJobs/lifecycle skew, transient GitHub/root errors, reservation expiry, root crash boundaries and cleanup failure.
- Verify all nine runner classes and 23 routes against the state-machine model and migration-equivalence matrix.
- Prototype runner-class maintenance/reconciliation projections and prove no cpu/gpu lane grammar or live activation leakage remains.
- Only after repository-only protocol verification passes, design a separately authorized one-class-at-a-time live migration.

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
