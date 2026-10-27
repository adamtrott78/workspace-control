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
- Remote checkpoint: 103c97e844647bb7fc234761fc17c7bbb829be3f
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Validate the BF-3 correction on exact code checkpoint 103c97e844647bb7fc234761fc17c7bbb829be3f without redundant manual reruns. Verify scripts/lambda_ci_runtime.py now consumes the root-authored launch spec forbidden_paths and emits deterministic systemd InaccessiblePaths for the exact manifest set, rejects malformed/duplicate/conflicting deny paths, preserves workspace-control's own required roots, and that adversarial tests prove sibling project roots and descendant trusted-cache paths are inaccessible. If the exact checkpoint validation passes, freeze the new implementation blobs and request a fresh independent implementation review focused on BF-3 plus regression of the previously accepted BF-1/BF-2 and scope/resource boundaries. Do not install, reconcile, activate, or trigger P1 before NO_BLOCKING_FINDING.

## Remaining work

- Obtain and durably consume an independent implementation review of PR #521, explicitly covering BF-1 stale-assignment/reset/retry semantics, BF-2 maintenance authority/non-circularity/receipts, workspace-control isolation/resource envelope, and all deferred P2/P3 boundaries.
- If and only if the implementation review returns NO_BLOCKING_FINDING, perform bounded P1 installation/activation using the exact reviewed implementation and preserve a known-good bootstrap/rollback path.
- Validate live P1 with owner-commanded same-repository PR-head execution, CPU/RAM/runtime envelope, no-GPU/forbidden-path isolation, deterministic receipts, stale-assignment recovery dry-run/contract proof, maintenance authorization, and rollback.
- Do not raise maxRunners or manifest concurrency until separately reviewed resource-aware host arbitration is designed and validated.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, hosted/bootstrap fallback removal, and temporary transport cleanup unauthorized.

## Blockers / gates

- BF-3 from independent implementation review 5661642118: workspace-control forbidden-path isolation must be enforced at the privileged runner launch boundary. Correction is implemented at code checkpoint 103c97e844647bb7fc234761fc17c7bbb829be3f and awaits exact-checkpoint repository validation plus fresh independent re-review before any P1 installation/activation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
