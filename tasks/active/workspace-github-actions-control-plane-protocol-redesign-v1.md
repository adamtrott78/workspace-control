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
- Remote checkpoint: 2480a1321ebf65a13d77d7d31443314fbfb95cd2
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

LIVE MIGRATION IS PARTIALLY COMPLETE. Do NOT repeat Input #1 or Input #2. The latest Lambda Input #3 attempt using prior operator f7ac4e66313928c2f6d334a446bb30e4da160737 failed safely before any canary authority creation, v2 quiesce, v3 class activation, or workflow dispatch. Live output proved reconciler/provisioner ACTIVE and disabled, all nine v3 class controllers INACTIVE and disabled, legacy Research GPU INACTIVE, PREFLIGHT_NO_CANARY_AUTHORITY_CONSUMPTION=PASS, and PREFLIGHT_NO_CANARY_TRANSACTION_RECEIPT=PASS. The exact failure was the installed older gh CLI rejecting gh run list --event during CANARY_RUN_HISTORY_CHECK; STOP_CANARY_RUN_HISTORY_QUERY_FAILED rc=1. The corrected operator is exact substantive head 2480a1321ebf65a13d77d7d31443314fbfb95cd2, script blob 1b36bd64311fc7e45f56909a356c41a856fb0f85, Workspace Control Validation #1367 / run 41257124698 SUCCESS. It removes all gh run and gh workflow run subcommand dependencies: workflow ID resolution, history checks, dispatch, run discovery, terminal polling, and cancellation use gh api REST endpoints only. Next safe action: execute exactly scripts/lambda_ci_v3_first_canary_live.sh from head 2480a1321ebf65a13d77d7d31443314fbfb95cd2 on Lambda. Any STOP marker is terminal for that attempt and must not be blindly retried; otherwise allow exactly one workspace-control-control-small-v1 canary and exact v2 prestate rollback.

## Remaining work

- Execute the exact-head-green corrected Input #3 operator at 2480a1321ebf65a13d77d7d31443314fbfb95cd2. It must re-prove live root/class/containment state, no canary authority/transaction residue, resolve the exact canary workflow ID through the REST API, prove zero prior canary runs, and clean/stage credentials before creating authority.
- Complete exactly one workspace-control-control-small-v1 generation-exclusion canary: create one-shot authority, prove v2 drain, activate only target v3 controller, dispatch only the owner-only canary through the REST API, require terminal success, prove v3 execution/resource drain, then restore exact captured v2 prestate.
- After accepted first canary, advance additional public-network classes only in frozen migration order under separately accepted live authority.
- Keep all Research GPU-derived classes NO_BY_DEFAULT until separate containment-recovery authority; keep Research Engine PR #283 proposal-only until separate default-branch producer cutover authority.
- Only after accepted class canaries may old scale-set drain/retirement and broader production activation be separately authorized.

## Blockers / gates

- One operator action on Lambda is required to execute the exact corrected Input #3 operator at 2480a1321ebf65a13d77d7d31443314fbfb95cd2. The prior attempt failed safely because the installed gh CLI lacks gh run list --event/--branch support; the corrected operator now uses gh api REST endpoints for all Actions run control.
- Lambda root services are already live from successful Input #2: workspace-ci-v3-reconciler.service and workspace-ci-v3-provisioner.service must remain active/attested; do not repeat ACTIVATE_V3_ROOT_SERVICES or create a competing root activation receipt.
- All Research GPU-derived runner classes remain inherited-contained and NO_BY_DEFAULT. Do not start workspace-ci-controller@research-engine-gpu.service, restore retry authority, or advance any Research GPU-derived v3 class.
- Research Engine PR #283 remains draft/proposal-only at exact head 6165556086b73d2076f205f11ec7b988150f23dd; no default-branch producer cutover is authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
