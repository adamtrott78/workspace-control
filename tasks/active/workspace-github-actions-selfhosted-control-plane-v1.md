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

Post exactly one owner-authored maintenance comment on workspace-control issue #527 with the single-line body `/workspace-ci-maintain diagnose workspace-control cpu`. Record the immutable comment ID. Then perform only read-only inspection of `/var/lib/workspace-ci/maintenance-controller/receipts/<comment_id>.json` after the controller poll to prove status COMPLETED, exact identity/source attestation, operation DIAGNOSE_LANE, installed policy digests, and bounded diagnosis result. Do not post a second maintenance command and do not reconcile, activate workspace-control, restart/reset any controller, or restart research-engine CPU before that receipt is durably accepted.

## Remaining work

- Post exactly one owner-authored `/workspace-ci-maintain diagnose workspace-control cpu` comment on maintenance issue #527 and capture its immutable GitHub comment ID.
- After the maintenance controller polls it, read only the corresponding `/var/lib/workspace-ci/maintenance-controller/receipts/<comment_id>.json` durable receipt and any bounded root diagnosis fields needed to prove DIAGNOSE_LANE acceptance; do not issue a second command.
- Only after the diagnostic receipt is accepted, independently gate workspace-control activation as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- Corrected P1 bootstrap from reviewed executable checkpoint 9b402da8c0158be477ac00944b5c164ddef81193 succeeded with decision PASS. L0 maintenance root/controller are commissioned and active; no maintenance command has yet been executed.
- The next gate is exactly one owner-authored `/workspace-ci-maintain diagnose workspace-control cpu` comment on maintenance issue #527, followed by read-only proof of the durable local maintenance-controller receipt and bounded root DIAGNOSE_LANE result.
- workspace-control activation remains blocked until that exact GitHub -> L0 diagnostic command completes with an accepted durable receipt. No reconciliation, activation, restart, reset-stale, P2/P3, or capacity widening is authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
