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
- Remote checkpoint: 92cbea0e71b3992f9a399b388a1884bbd3ce13a8
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

LIVE MIGRATION IS PARTIALLY COMPLETE. Do NOT repeat Input #1 or Input #2. The latest Lambda Input #3 attempt from current validated head fcc925a43449f12c402de60fa7257498f3a9a3f1 again failed safely before canary authority creation or generation exclusion. It re-proved root/class/containment state, no canary authority consumption, no transaction receipt, exact workflow id 401444238, zero prior canary runs, installed generation binding, exact transaction helper, Go 1.26.3, v3-canary-preflight build, and credential reset. Primary raw-token export via `gh auth token` failed rc=1; fallback `gh auth status --show-token` did not expose exactly one unmasked token and stopped with STOP_GH_AUTH_STATUS_TOKEN_PARSE_FAILED. A direct authenticated probe `gh api user --jq .login` then returned adamtrott78 with rc=0, proving the existing GitHub credential is valid; the blocker is the outdated GitHub CLI's token-export interface, not token expiry. GitHub currently recommends its official Debian/Ubuntu packages and notes that older community 2.45/2.46 packages are broken; the official Linux repository also rotated signing keys in 2026. Next safe action: update the Lambda host's `gh` from GitHub's official apt repository with the current keyring, verify `gh auth token` succeeds without printing the token and `gh api user` returns adamtrott78, then retry the same exact validated Input #3 operator. Any STOP marker remains terminal for that attempt.

## Remaining work

- Refresh the official GitHub CLI apt keyring/repository on Lambda and upgrade gh. Verify the installed version and that `gh auth token` succeeds without printing the token while `gh api user --jq .login` returns adamtrott78.
- Retry the exact-head-green Input #3 operator from fcc925a43449f12c402de60fa7257498f3a9a3f1 / script blob 44ce0c0edc07b67354b0e7abafc0fa1b01353911. It must re-prove all live invariants before creating authority.
- Complete exactly one workspace-control-control-small-v1 generation-exclusion canary: create one-shot authority, prove v2 drain, activate only target v3 controller, dispatch only the owner-only canary through REST, require terminal success, prove v3 execution/resource drain, then restore exact captured v2 prestate.
- After accepted first canary, advance additional public-network classes only in frozen migration order under separately accepted live authority.
- Keep all Research GPU-derived classes NO_BY_DEFAULT until separate containment-recovery authority; keep Research Engine PR #283 proposal-only until separate default-branch producer cutover authority.

## Blockers / gates

- The installed Lambda GitHub CLI can authenticate successfully (`gh api user` -> adamtrott78, rc=0) but cannot export the raw token through either `gh auth token` or the attempted legacy `gh auth status --show-token` path. Upgrade gh from GitHub's official apt repository before retrying Input #3.
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
