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

Validate the final PR #599 head containing BF-1/BF-2 corrections plus durable task binding. If green, issue a new authority-sensitive review request superseding request 6798274468 / blocked disposition 6798416097. The bounded live transaction remains unchanged in scope, but the reviewer must verify exact integer lineage decoding and validate-before-delete semantics for reset-zero evidence before accepting.

## Remaining work

- Validate the final corrected PR #599 head after this durable task binding.
- Obtain fresh independent authority-sensitive review proving BF-1/BF-2 closure and accepting the bounded live transaction.
- Execute the reviewed controller+manifest+historical recovery-state repair only after exact live preflight.
- Prove workspace-control CPU stable running, stale quarantine retired by the fixed controller, recovery gate terminal, and sibling semantic state preserved.
- Allow existing exact-head run #389 to proceed naturally and record its result.

## Blockers / gates

- Fresh exact-head validation is required after this BF-1/BF-2 task-state binding.
- Fresh authority-sensitive review is required on the final corrected PR #599 head before installing the controller or mutating historical workspace-control recovery state.
- Live repair remains bound to exact historical quarantine receipt ab2334ab-384c-4432-ab84-f5b38ba4071d, old scale set 1 -> new scale set 3, reset generation 40d61b30-e8b9-5559-abfc-706fb3df6c67, and terminal probe run/job 41404080844/125142056183.
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
