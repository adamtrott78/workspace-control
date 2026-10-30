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
- Remote checkpoint: d7de132c7cadc620905b5a827f391d1bc8786dd0
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 6165556086b73d2076f205f11ec7b988150f23dd
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 35e6f451fe36f039b5f6461f7469f0eed1e79e43
- Remote verified: true

## Next safe action

Repository-only v3 offline payload isolation and cross-repo producer evidence are exact-head green at workspace-control@d7de132c7cadc620905b5a827f391d1bc8786dd0 (Workspace Control Validation #1332 / run 41008189246). Research Engine draft PR #283 is exact head 6165556086b73d2076f205f11ec7b988150f23dd on repaired main 1031861c03b2af8cff5cf72939bbbc83a95e65a4; hosted CI #642 / run 41007835081 executed repository steps and passed compile, full tests, Compose validation, daemon image build, and cleanup, with exact-head acceptance comment 6515645161. The hosted-CI gate is resolved. Continue only with repository-safe review/preparation unless separate authority is granted. Do not merge/cut over PR #283, mutate Lambda, activate v3, dispatch migration canaries, or alter Research GPU containment/retry authority without the corresponding explicit authority.

## Remaining work

- Keep Research Engine PR #283 proposal-only until a separately authorized production workflow cutover binds the exact merged default-branch blobs into controller projections/deployment generation according to architecture/lambda-ci-v3-offline-producer-cutover-plan.v1.json.
- Obtain separate explicit live authority before any Lambda mutation; the migration plan currently grants NONE.
- Under that authority, install only the exact inactive v3 substrate candidate, verify generated identities/policies/systemd/tmpfiles/state and root/reconciler health, including root-owned /run/workspace-ci-v3-payload, with all nine class controllers still inactive.
- Deploy and bind the exact generated owner-only migration canary workflow/policy for workspace-control-control-small-v1, then execute the generation-exclusion transaction: stop/drain all v2 project controllers before starting exactly one v3 class controller, without dispatching from the transaction helper.
- Collect exact canary receipt and rollback/restore proof; preserve Research GPU quarantine and invalidated retry authority throughout.
- Advance additional public-network classes only under separate accepted live authority and in the frozen migration order; Research GPU-derived classes remain NO_BY_DEFAULT until separate containment recovery authority.
- For the two offline Research model classes, require accepted live canaries, separate Research GPU containment-recovery authority, and separate default-branch cutover authority before any production route activation; hosted producer CI #642 is already accepted.
- Only after accepted class canaries may old scale-set drain/retirement and broader live activation be separately authorized.

## Blockers / gates

- Live migration remains deliberately unauthorized: architecture/lambda-ci-v3-migration-plan.v1.json still grants live_authority=NONE. No v3 substrate, root service, class controller, canary workflow or migration transaction has been installed/activated on Lambda.
- All Research GPU-derived runner classes, including research-model-single-offline-v1 and research-model-dual-offline-v1, remain inherited-contained and NO_BY_DEFAULT until separate recovery/live authority explicitly consumes the legacy containment boundary.
- Research Engine PR #283 remains draft/proposal-only at exact head 6165556086b73d2076f205f11ec7b988150f23dd. Hosted CI #642 is accepted repository evidence, but the reviewed workflow blobs are not on the default branch or in production trusted-workflow evidence, and no default-branch producer cutover authority has been granted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
