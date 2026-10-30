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
- Remote checkpoint: c0fd0b10cac51e3ace3f988132cdeec661d3a905
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

Implement and repository-verify the production v3 root capacity provider, v3 runner-class controller, v3 reconciliation/systemd install surface, and migration-canary/cutover tooling under disjoint paths on PR #572. Do not mutate Lambda, start v3 controllers, apply PR #571, retrigger host-attest, or alter research-engine GPU containment.

## Remaining work

- Implement a production v3 root capacity provider from the verified two-phase RESERVE/LAUNCH/STATUS/CANCEL model under disjoint v3 paths.
- Implement a production v3 Go runner-class controller using the pinned actions/scaleset client, TotalAssignedJobs scaling, structured trusted-workflow admission, in-process retry/backoff, and no JobDisplayName parser.
- Implement v3 reconciliation/install projections, unique controller Unix identities, project credential groups, systemd templates, tmpfiles, and disjoint persistent/runtime state.
- Generate migration-only class canary workflows and prove their payloads cannot execute candidate code or widen class authority.
- Add repository-only integration tests proving v2/v3 install-path disjointness and the generation-exclusion cutover/rollback transaction.
- Only after the production implementation candidate and migration transaction are exact-head green may any separate live activation authority be considered.

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
