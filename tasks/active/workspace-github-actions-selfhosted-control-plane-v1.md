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
- Remote branch: main
- Remote checkpoint: 4d98555a678050e611502de1b9b8c35b4cf9c5fa
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Validate the final PR #598 head. If green, request fresh authority-sensitive review of the exact head plus the bounded live transaction already described on PR #598: source-attest exact reviewed head/base; prove installed manifest semantic equality to the exact base manifest; preserve exact installed controller/unit/maintenance/provisioner/runtime/root-policy identities and sibling states; stop only workspace-control CPU; atomically replace only /etc/workspace-ci/projects/workspace-control.json with the reviewed target manifest; do not restart provisioner; reset-failed/start only workspace-control CPU if needed; require stable running with unchanged InvocationID/NRestarts across the bounded observation window and unchanged sibling semantic snapshots; allow existing run #389 to proceed without cancel/retrigger; rollback by restoring only the old manifest and leaving workspace-control CPU stopped on any post-backup failure.

## Remaining work

- Validate the final PR #598 head containing manifest repair, regression, and durable task binding.
- Obtain fresh authority-sensitive review of the exact head and bounded one-file live installed-manifest transaction.
- Stop only workspace-control CPU, atomically replace only /etc/workspace-ci/projects/workspace-control.json, then start only workspace-control CPU.
- Prove bounded stable-running controller health and exact sibling semantic-state preservation.
- Observe existing run #389 naturally acquire a runner and complete; do not retrigger it.

## Blockers / gates

- Fresh authority-sensitive review is required on the final PR #598 head after this task-state binding and on the bounded one-file live repair transaction.
- Live installed manifest must semantically equal the exact pre-repair base manifest before replacement; any drift aborts.
- Any live identity/state mismatch aborts before mutation. No reconcile, provisioner restart, sibling mutation, scale-set operation, workflow cancel/retrigger, or admission/capacity widening is authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
