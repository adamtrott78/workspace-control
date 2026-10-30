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
- Remote checkpoint: 601ca411ea14045944b503a6abc70ef4aadf86d2
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 5439c2a38648531b995ead92f54e5ab9de55f511
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 35e6f451fe36f039b5f6461f7469f0eed1e79e43
- Remote verified: true

## Next safe action

Repository-only v3 offline payload separation, migration-canary proof, cross-repo producer binding, and future default-branch cutover/rollback design are exact-head green at workspace-control@601ca411ea14045944b503a6abc70ef4aadf86d2 (Workspace Control Validation #1320 / run 41003165205; durable PR #572 receipt comment 6515017656). Research Engine producer changes remain isolated in draft PR #283 at 5439c2a38648531b995ead92f54e5ab9de55f511 (repository-only review comment 6514972948). The only repository-safe unresolved validation is obtaining a private-repo GitHub-hosted CI attempt that actually allocates a runner and executes steps. Do not merge/cut over PR #283, mutate Lambda, activate v3, dispatch migration canaries, or alter Research GPU containment/retry authority without separate explicit authority.

## Remaining work

- Obtain a Research Engine PR #283 GitHub-hosted CI run that actually allocates a runner and executes repository steps; run 41002055202 has failed before runner allocation on three attempts and provides no code/test result.
- Keep PR #283 proposal-only until a separately authorized production workflow cutover binds the exact merged default-branch blobs into controller projections/deployment generation according to architecture/lambda-ci-v3-offline-producer-cutover-plan.v1.json.
- Obtain separate explicit live authority before any Lambda mutation; the migration plan currently grants NONE.
- Under that authority, install only the exact inactive v3 substrate candidate, verify generated identities/policies/systemd/tmpfiles/state and root/reconciler health, with all nine class controllers still inactive.
- Deploy and bind the exact generated owner-only migration canary workflow/policy for workspace-control-control-small-v1, then execute the generation-exclusion transaction: stop/drain all v2 project controllers before starting exactly one v3 class controller, without dispatching from the transaction helper.
- Collect exact canary receipt and rollback/restore proof; preserve Research GPU quarantine and invalidated retry authority throughout.
- Advance additional public-network classes only under separate accepted live authority and in the frozen migration order; Research GPU-derived classes remain NO_BY_DEFAULT until separate containment recovery authority.
- For the two offline Research model classes, require both accepted live canaries and the separate producer/default-branch cutover authority before any production route activation.
- Only after accepted class canaries may old scale-set drain/retirement and broader live activation be separately authorized.

## Blockers / gates

- Live migration remains deliberately unauthorized: architecture/lambda-ci-v3-migration-plan.v1.json still grants live_authority=NONE. No v3 substrate, root service, class controller, canary workflow or migration transaction has been installed/activated on Lambda.
- All Research GPU-derived runner classes, including research-model-single-offline-v1 and research-model-dual-offline-v1, remain inherited-contained and NO_BY_DEFAULT until separate recovery/live authority explicitly consumes the legacy containment boundary.
- Research Engine PR #283 remains draft/proposal-only and its exact workflow blobs are not on the default branch or in production trusted-workflow evidence. GitHub-hosted CI run 41002055202 failed before runner allocation on three attempts (ubuntu-latest, runner_id=0, zero steps), so an actual hosted CI execution is still required before any default-branch cutover review can be accepted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
