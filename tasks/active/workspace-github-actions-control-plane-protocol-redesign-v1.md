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
- Remote checkpoint: f7ac4e66313928c2f6d334a446bb30e4da160737
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

LIVE MIGRATION IS PARTIALLY COMPLETE. Do NOT repeat Input #1 or Input #2. The corrected Input #3 operator is exact head f7ac4e66313928c2f6d334a446bb30e4da160737, script blob 06ea115cdf1156f534a98829b140b74c59463bff, and Workspace Control Validation #1364 / run 41019685530 is SUCCESS. The prior silent failure cannot be distinguished post hoc between the bare Go build and immediately following credential-staging commands because the old script emitted no per-step terminal marker and cleanup removed its temporary state. The corrected operator now fails loudly for every Go toolchain/build and ephemeral gh-token credential-staging command; it also re-proves root-service active/non-enabled state, all nine v3 class controllers inactive/non-enabled, Research GPU legacy containment, absence of canary-specific authority consumption/transaction residue, zero prior migration-canary workflow runs, and deliberate credential reset before creating any new authority. Public GitHub evidence currently shows zero workflow_dispatch runs on main. Next safe action: execute exactly scripts/lambda_ci_v3_first_canary_live.sh from head f7ac4e66313928c2f6d334a446bb30e4da160737 on Lambda. If any preflight/diagnostic STOP marker appears, do not retry blindly; return that exact output. If all preflight gates pass, the same bounded operator may proceed with exactly one workspace-control-control-small-v1 canary and exact v2 prestate rollback.

## Remaining work

- Execute the exact-head-green corrected Input #3 operator at f7ac4e66313928c2f6d334a446bb30e4da160737. It must first re-prove live root/class/containment state, no canary authority/transaction residue, zero prior canary runs, and clean credential staging; any STOP marker is terminal for that attempt.
- Complete exactly one workspace-control-control-small-v1 generation-exclusion canary: create one-shot authority, prove v2 drain, activate only target v3 controller, dispatch only the owner-only canary, require terminal success, prove v3 execution/resource drain, then restore exact captured v2 prestate.
- After accepted first canary, advance additional public-network classes only in frozen migration order under separately accepted live authority.
- Keep all Research GPU-derived classes NO_BY_DEFAULT until separate containment-recovery authority; keep Research Engine PR #283 proposal-only until separate default-branch producer cutover authority.
- Only after accepted class canaries may old scale-set drain/retirement and broader production activation be separately authorized.

## Blockers / gates

- One operator action on Lambda is now required to execute the exact corrected Input #3 operator at f7ac4e66313928c2f6d334a446bb30e4da160737. No further repository-only evidence can identify the old silent command because the prior script had no per-step marker and removed temporary state on exit.
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
