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
- Current stage: bounded_migration_and_live_acceptance

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 455f0585d9006435335112ca896af7671a0f9f64
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

## Exact repository-only boundary

- PR #572 exact head 455f0585d9006435335112ca896af7671a0f9f64
- Workspace Control Validation #1293 / run 40999275931: SUCCESS
- Production v3 root provider: repository verified, not installed
- Separate v3 Go runner-class controller: repository verified, not activated
- Inactive v3 install/reconciliation substrate: repository verified, not applied
- Migration-only canary generator/probe: repository verified, staged only
- One-class generation-exclusion cutover/rollback transaction: repository verified, not run
- Lambda mutations in this boundary: none
- Live migration authority: NONE

## Next safe action

Repository-only production v3 implementation and the one-class generation-exclusion canary transaction are exact-head green at 455f0585d9006435335112ca896af7671a0f9f64 (Workspace Control Validation #1293 / run 40999275931). The next step requires separate operator/live authority; do not mutate Lambda until such authority is explicitly issued. If authorized, begin only with the inactive v3 substrate/root-reconciler preparation and the first migration-order canary (workspace-control-control-small-v1), using an exact-generation root-owned authorization receipt and the generated owner-only canary workflow/policy. Preserve all Research GPU containment/retry invalidation. Do not authorize the two offline model classes until payload-network isolation is separately implemented and proven.

## Remaining work

- Obtain separate explicit live authority before any Lambda mutation; the migration plan currently grants NONE.
- Under that authority, install only the exact inactive v3 substrate candidate, verify generated identities/policies/systemd/tmpfiles/state and root/reconciler health, with all nine class controllers still inactive.
- Deploy and bind the exact generated owner-only migration canary workflow/policy for workspace-control-control-small-v1, then execute the generation-exclusion transaction: stop/drain all v2 project controllers before starting exactly one v3 class controller, without dispatching from the transaction helper.
- Collect the exact canary receipt and rollback/restore proof; preserve Research GPU quarantine and invalidated retry authority throughout.
- Advance additional public-network classes only under separate accepted live authority and in the frozen migration order; Research GPU-derived classes remain NO_BY_DEFAULT.
- Design, implement and prove process/network separation for GITHUB_CONTROL_PLANE_ONLY_PAYLOAD_OFFLINE before either offline model class can enter live acceptance.
- Only after accepted class canaries may production workflow route cutover, old scale-set drain/retirement and broader live activation be separately authorized.

## Blockers / gates

- Live migration remains deliberately unauthorized: architecture/lambda-ci-v3-migration-plan.v1.json still grants live_authority=NONE. No v3 substrate, root service, class controller, canary workflow or migration transaction has been installed/activated on Lambda.
- research-model-single-offline-v1 and research-model-dual-offline-v1 declare GITHUB_CONTROL_PLANE_ONLY_PAYLOAD_OFFLINE, but the current shared runner cgroup can restrict private/link-local networks only and cannot separate GitHub control-plane traffic from arbitrary public payload egress. Both classes remain blocked; they are also within inherited Research GPU containment.

## Fresh-chat initialization

@GitHub
@Heartbeat

https://github.com/adamtrott78/workspace-control

Continue durable task:
workspace-github-actions-control-plane-protocol-redesign-v1

Start from the authoritative capsule:
tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

PR #572 branch:
github-actions-control-plane-protocol-redesign-v1

Repository-only production v3 and the generation-exclusion canary transaction are exact-head green at 455f0585d9006435335112ca896af7671a0f9f64, Validation #1293 / run 40999275931. Do not redo architecture/modeling. Do not mutate Lambda unless separate live authority is explicitly supplied. Preserve Research GPU containment and the offline-model network-isolation blocker.
