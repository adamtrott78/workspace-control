<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-selfhosted-control-plane-v1
- Title: GitHub Actions Self-Hosted Control Plane v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Eliminate routine dependence on metered GitHub-hosted runners by moving workspace-control and project CI onto bounded self-hosted Lambda execution while preserving a non-circular bootstrap authority, per-project isolation, fail-closed admission, review gates, and a clean path to GitHub organization runner groups. Also reduce operator copy/paste by making review targets and dispositions durable and GitHub-native.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-selfhosted-control-plane-v1
- Remote checkpoint: fc3bbdaded02625f968b18d504caa3ce52d3bb18
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 15c2f98feb980f18fac255b74c6a39db5da4ef30
- Remote verified: true

## Next safe action

Current emergency path: do not create duplicate exact-provenance validation runs. Wait for superseded run 40266278120 to become terminal, then trigger exactly one `/validate-exact-provenance-binding 3eb6b391fcd2f6e2a44277771d0bcd8d26c7002d` run using the reconciled network-free trusted workflow blob ac03ea6196ae1b427e5f3c608e5ce5fb18704e1e and require terminal implementation-validation PASS before authorizing the one preregistered scientific trigger. In parallel, PR #508 remains design-only and independently unreviewed; do not activate a workspace-control runner from that design until independent disposition.

## Remaining work

- Obtain and durably consume independent review of exact v0.1 design/manifest.
- Restore the currently blocked reconciliation/EXTRACT validation chain using the temporary emergency capacity workaround.
- After NO_BLOCKING_FINDING, implement and validate the P1 owner-commanded workspace-control JIT pilot without moving bootstrap reconciliation authority.
- Design/review control-small and automatic pull_request/push admission as P2.
- Migrate routine hosted CI only after the pilot and automatic-event gates pass.
- Evaluate and separately execute GitHub organization migration with runner groups and least-privilege GitHub App credentials.
- Automate routine review request/consumption so the operator does not ferry text between chats.
- Treat stale GitHub scale-set assignment recovery as a required controller reliability fix: a controller restart must not leave TotalAssignedJobs>0 without authoritative recoverable job metadata indefinitely blocking the lane.
- Replace hard-coded maxRunners=1 and host-wide global serialization with separately reviewed bounded/resource-aware concurrency; preserve explicit GPU/CPU envelopes and fail-closed admission.
- Add trusted, owner-restricted remote maintenance/reconciliation actions for controller restart, reviewed profile installation, and bounded recovery so routine operations do not require operator shell copy/paste.

## Blockers / gates

- Live workspace-control self-hosted activation is blocked pending independent review of exact v0.1 design/manifest.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
