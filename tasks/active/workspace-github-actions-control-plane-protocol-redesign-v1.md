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
- Remote checkpoint: e8d879305ce8d016b06903cf3dc839861fe0e228
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

LIVE MIGRATION IS PARTIALLY COMPLETE. Do NOT repeat Input #1 or Input #2. The latest Lambda Input #3 attempt at prior head 7d324814aeca24e18ef6f1df51c9ecbcd958fbb1 failed safely before credential install, canary authority creation, generation exclusion, controller mutation, or workflow dispatch. Live output re-proved all preflight invariants and reached V3_WORKSPACE_CONTROL_GH_TOKEN_VERIFY=BEGIN after a successful `gh auth token` export, then stopped with STOP_GH_AUTH_TOKEN_VERIFY_FAILED rc=1. Root cause is now proven in the operator implementation: the compatibility patch used `tr -d '\\r\\n'`, which does not remove CR/LF, so the exported token was reinjected incorrectly; the fallback Python regex also used double-escaped whitespace classes. The corrected operator is exact head e8d879305ce8d016b06903cf3dc839861fe0e228, script blob 131b47b36cf3e5350a38e2a34f4614a40822fb09, Workspace Control Validation #1375 / run 41258778360 SUCCESS. It now reads the exported token byte-safely with `IFS= read -r`, verifies the exact token through GH_TOKEN, unsets it, and fixes the fallback regex. CI explicitly forbids the old bad escaped forms. Next safe action: execute exactly scripts/lambda_ci_v3_first_canary_live.sh from head e8d879305ce8d016b06903cf3dc839861fe0e228 on Lambda. Any STOP marker is terminal for that attempt; otherwise allow exactly one workspace-control-control-small-v1 canary and exact v2 prestate rollback.

## Remaining work

- Execute the exact-head-green corrected Input #3 operator at e8d879305ce8d016b06903cf3dc839861fe0e228 / script blob 131b47b36cf3e5350a38e2a34f4614a40822fb09. It must re-prove all live invariants before creating authority.
- Complete exactly one workspace-control-control-small-v1 generation-exclusion canary: create one-shot authority, prove v2 drain, activate only target v3 controller, dispatch only the owner-only canary through REST, require terminal success, prove v3 execution/resource drain, then restore exact captured v2 prestate.
- After accepted first canary, advance additional public-network classes only in frozen migration order under separately accepted live authority.
- Keep all Research GPU-derived classes NO_BY_DEFAULT until separate containment-recovery authority; keep Research Engine PR #283 proposal-only until separate default-branch producer cutover authority.

## Blockers / gates

- One operator action on Lambda remains: execute corrected Input #3 head e8d879305ce8d016b06903cf3dc839861fe0e228. The prior token-verification stop was caused by a double-escaping bug in the operator, not by GitHub authentication or token expiry.
- Lambda root services are already live from successful Input #2; do not repeat ACTIVATE_V3_ROOT_SERVICES.
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
