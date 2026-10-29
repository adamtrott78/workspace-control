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
- Remote checkpoint: 620cf09b1140b6fde88bf2ae9cb8c5241aaebcb4
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

Complete canonical_protocol_and_state_machine on PR #572: freeze runner-class local authentication, capacity request/response semantics, retry/ack rules, and generated controller/root policy projections. Do not apply PR #571 parser hotfix to Lambda, restart project controllers, retrigger host-attest, or mutate research-engine/PADataset runtime state.

## Remaining work

- Finalize the canonical runner-class capacity protocol and local controller authentication mechanism.
- Freeze the class-specific controller policy projection and root runner-class projection generated from one catalog.
- Define exact retry/backoff/ack behavior for transient GitHub, JIT, and root transport failures without using systemd restart as request retry.
- Model and test controller restart, message redelivery, GitHub reassignment, root restart, JIT orphan cleanup, class quarantine, and scale-set migration.
- Design generated executor command builders and migrate maintenance targeting from cpu/gpu lane to runner_class_id.
- Design repository-only compatibility/property/state-machine tests covering all 23 registered routes and all nine proposed runner classes.
- Only after repository-only verification, design bounded migration from the five current scale sets to the nine homogeneous runner-class scale sets.

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
