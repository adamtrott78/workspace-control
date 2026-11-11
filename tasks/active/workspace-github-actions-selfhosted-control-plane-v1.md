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

Validate the final PR #599 head. If green, request fresh authority-sensitive review of: (1) the crash-safe controller fix; and (2) a bounded live repair that source-attests the exact reviewed head, proves the installed old controller/manifest identities, proves stale quarantine receipt ab2334ab-384c-4432-ab84-f5b38ba4071d is workspace-control/cpu/lambda-workspace-control/scale-set 1, proves the matching recovery gate is RECOVERY_RETRY_ACQUIRED for old scale set 1 -> new scale set 3 with reset generation 40d61b30-e8b9-5559-abfc-706fb3df6c67 and job/run 125142056183/41404080844, proves that GitHub run/job terminal failure, closes only that historical gate to RECOVERY_RETRY_COMPLETED, installs only the reviewed controller binary and reviewed workspace-control manifest, starts only workspace-control CPU, and proves stable running/sibling preservation. No reset/reconcile/retrigger is authorized.

## Remaining work

- Validate final PR #599 head with durable task binding.
- Obtain fresh independent authority-sensitive review of the controller fix and bounded live recovery-state repair.
- Install the reviewed controller binary and reviewed workspace-control manifest binding only after exact source/installed-state preflight.
- Close only the stale historical RECOVERY_RETRY_ACQUIRED gate after exact terminal run/job proof, then let the fixed controller retire the matching old quarantine safely.
- Start only workspace-control CPU and prove stable running plus sibling preservation.
- Allow existing exact-head run #389 to proceed naturally and record its result.

## Blockers / gates

- Fresh exact-head validation is required after this task-state binding.
- Fresh authority-sensitive review is required before installing the repaired controller or mutating the historical workspace-control recovery-state files.
- Live repair must prove exact stale quarantine receipt ab2334ab-384c-4432-ab84-f5b38ba4071d bound to old scale set 1, exact matching recovery gate bound to new scale set 3/reset generation 40d61b30-e8b9-5559-abfc-706fb3df6c67, and exact terminal GitHub probe run/job identity before any state mutation.
- No scale-set reset/recreation, reconciliation, provisioner restart, sibling-controller mutation, workflow cancel/retrigger, admission/capacity widening, or research-engine mutation is authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
