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

LIVE MIGRATION IS PARTIALLY COMPLETE. Do NOT repeat Input #1 or Input #2. The latest Lambda Input #3 attempt at prior substantive head 2480a1321ebf65a13d77d7d31443314fbfb95cd2 failed safely before canary authority creation or generation exclusion. Live output proved both v3 root services ACTIVE and boot-disabled, all nine v3 class controllers INACTIVE and disabled, legacy Research GPU INACTIVE, no ACTIVATE_ONE_V3_CANARY consumption marker, no canary transaction receipt, exact owner-only canary workflow ID 401444238 resolved, zero prior canary runs, installed generation binding PASS, exact migration helper materialization PASS, Go 1.26.3 verification PASS, v3-canary-preflight build PASS, and credential reset PASS. The exact failure was STOP_GH_AUTH_TOKEN_EXPORT_FAILED rc=1 at the newer `gh auth token` command. The corrected operator is exact head 92cbea0e71b3992f9a399b388a1884bbd3ce13a8, script blob 44ce0c0edc07b67354b0e7abafc0fa1b01353911, Workspace Control Validation #1370 / run 41257730195 SUCCESS. It first tries `gh auth token`; if unsupported, it securely captures `gh auth status --hostname github.com --show-token` into a mode-0600 temp file, parses exactly one unmasked token without printing it, verifies that exported token through `gh api user` as login adamtrott78, then stages it root:ci-gh-workspace-control 0640. Next safe action: execute exactly scripts/lambda_ci_v3_first_canary_live.sh from head 92cbea0e71b3992f9a399b388a1884bbd3ce13a8 on Lambda. Any STOP marker is terminal for that attempt; otherwise allow exactly one workspace-control-control-small-v1 canary and exact v2 prestate rollback.

## Remaining work

- Execute the exact-head-green corrected Input #3 operator at 92cbea0e71b3992f9a399b388a1884bbd3ce13a8. It must re-prove all live preflight invariants and use the legacy-safe token export fallback if `gh auth token` is unavailable.
- Complete exactly one workspace-control-control-small-v1 generation-exclusion canary: create one-shot authority, prove v2 drain, activate only target v3 controller, dispatch only the owner-only canary through REST, require terminal success, prove v3 execution/resource drain, then restore exact captured v2 prestate.
- After accepted first canary, advance additional public-network classes only in frozen migration order under separately accepted live authority.
- Keep all Research GPU-derived classes NO_BY_DEFAULT until separate containment-recovery authority; keep Research Engine PR #283 proposal-only until separate default-branch producer cutover authority.
- Only after accepted class canaries may old scale-set drain/retirement and broader production activation be separately authorized.

## Blockers / gates

- One operator action on Lambda is required to execute exact corrected Input #3 head 92cbea0e71b3992f9a399b388a1884bbd3ce13a8. The prior attempt failed safely because the installed gh CLI does not support the newer `gh auth token` command; the corrected operator has a secret-safe legacy `gh auth status --show-token` fallback and verifies the exported identity before staging.
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
