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
- Remote checkpoint: 28c8b9e091d108b6168b32409146e99b75ad150f
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Continue the permanent GitRunner/self-hosted control-plane task, not EXTRACT science. Independently review PR #508 against the exact frozen v0.1 architecture blob f70f100ba57140469ff656255de00f7de262dbc3 and NOT_INSTALLED workspace-control manifest blob efa6e09f4206ca1d1d2fe6daaabcb69ed01d4588, explicitly incorporating runtime-evidence comments 6405597751 and 6408089808. Persist either NO_BLOCKING_FINDING or exact blocking findings. Do not activate a workspace-control runner before that disposition. If review is clean, implement only the P1 owner-commanded workspace-control JIT validation pilot while leaving bootstrap reconciliation authority independent. If runtime evidence blocks v0.1, revise/freeze a bounded v0.2 and re-review before implementation. Do not continue workspace-local-extract-independent-review-v1 inside this task.

## Remaining work

- Obtain and durably consume independent review of exact v0.1 design/manifest.
- After the independent review, explicitly decide whether the observed stale-assignment, single-slot queue poisoning, global host serialization, and operator-shell recovery evidence requires a reviewed v0.2 design before P1 activation.
- After NO_BLOCKING_FINDING, implement and validate the P1 owner-commanded workspace-control JIT pilot without moving bootstrap reconciliation authority.
- Design/review control-small and automatic pull_request/push admission as P2.
- Migrate routine hosted CI only after the pilot and automatic-event gates pass.
- Evaluate and separately execute GitHub organization migration with runner groups and least-privilege GitHub App credentials.
- Automate routine review request/consumption so the operator does not ferry text between chats.
- Treat stale GitHub scale-set assignment recovery as a required controller reliability fix: a controller restart must not leave TotalAssignedJobs>0 without authoritative recoverable job metadata indefinitely blocking the lane.
- Replace hard-coded maxRunners=1 and host-wide global serialization with separately reviewed bounded/resource-aware concurrency; preserve explicit GPU/CPU envelopes and fail-closed admission.
- Add trusted, owner-restricted remote maintenance/reconciliation actions for controller restart, reviewed profile installation, and bounded recovery so routine operations do not require operator shell copy/paste.
- Retire the temporary public workspace-control and GPU-listener transport workarounds only after a reviewed replacement path is live and rollback-safe.

## Blockers / gates

- Live workspace-control self-hosted activation is blocked pending independent review of exact v0.1 design/manifest plus the post-freeze runtime incident evidence on PR #508.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
