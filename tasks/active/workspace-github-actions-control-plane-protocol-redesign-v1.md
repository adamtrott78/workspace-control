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

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
