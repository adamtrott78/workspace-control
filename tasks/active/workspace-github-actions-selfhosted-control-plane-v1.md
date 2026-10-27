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
- Remote branch: gitrunner-p1-implementation
- Remote checkpoint: a9a3bf2c21a4c26d8dd1b52e2e81f15b85225f45
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Perform a fresh independent P1 implementation review of workspace-control PR #521. The exact implementation code checkpoint is a9a3bf2c21a4c26d8dd1b52e2e81f15b85225f45, validated by Workspace Control Validation run 40437708435 / job 121970360566. Review the exact implementation blobs recorded in this capsule and verify: BF-1 TotalAssignedJobs non-authority, durable assignment quarantine, exact stale-scale-set reset, duplicate replacement suppression, fresh scale-set identity, reset-pending quarantine, two complete zero-state observations >=15 seconds apart, policy-digest stability, controller-authored READY receipt, single-job recovery-generation consumption/completion, and maxRunners=1; BF-2 independent L0 maintenance path, SO_PEERCRED and owner/repository/comment attestation, fixed policy generation, typed verbs/derived targets only, installed policy digests, replay-safe COMPLETED/FAILED_CLOSED root receipts with rollback, no arbitrary shell/path/unit/property/credential/policy surface, and no direct L0 access to controller/provisioner/reconciler state. Re-check workspace-control MIGRATION_CANDIDATE_NOT_INSTALLED / PLANNED_NOT_BOUND state, concurrency=1, 200% CPU / 4G-8G / 10min / GPU0 envelope, same-repository owner-only workflow, isolation, independent bootstrap, and P2/P3 deferral. Return and durably record NO_BLOCKING_FINDING or exact actionable blockers. Do not install or activate P1 in the review task.

## Remaining work

- Obtain and durably consume an independent implementation review of PR #521, explicitly covering BF-1 stale-assignment/reset/retry semantics, BF-2 maintenance authority/non-circularity/receipts, workspace-control isolation/resource envelope, and all deferred P2/P3 boundaries.
- If and only if the implementation review returns NO_BLOCKING_FINDING, perform bounded P1 installation/activation using the exact reviewed implementation and preserve a known-good bootstrap/rollback path.
- Validate live P1 with owner-commanded same-repository PR-head execution, CPU/RAM/runtime envelope, no-GPU/forbidden-path isolation, deterministic receipts, stale-assignment recovery dry-run/contract proof, maintenance authorization, and rollback.
- Do not raise maxRunners or manifest concurrency until separately reviewed resource-aware host arbitration is designed and validated.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, hosted/bootstrap fallback removal, and temporary transport cleanup unauthorized.

## Blockers / gates

- P1 live installation/activation is blocked pending independent implementation review of PR #521 code checkpoint a9a3bf2c21a4c26d8dd1b52e2e81f15b85225f45 and exact implementation blobs.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
