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
- Remote checkpoint: 52b82bcb1c1fe8f9304be6c4e7cd7737b5c88227
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

LIVE MIGRATION IS PARTIALLY COMPLETE. Do NOT repeat inactive install or root-services activation. Lambda Input #1 PASS installed/attested v3 source generation 09c46818252991f6a55aaeedbcf046c554e2ffee with all nine class controllers inactive/disabled and Research GPU legacy controller inactive. Lambda Input #2 PASS consumed one-shot ACTIVATE_V3_ROOT_SERVICES authority 55f15dfe-a603-4901-b148-2aa11a2c0048 and left workspace-ci-v3-reconciler.service plus workspace-ci-v3-provisioner.service ACTIVE, provisioner socket valid, all class controllers inactive/disabled, and Research GPU containment preserved. Input #3 has NOT crossed the canary transaction boundary. Latest operator head 52b82bcb1c1fe8f9304be6c4e7cd7737b5c88227 passed Validation #1361/run 41018340472, but the live attempt exited silently during the pre-transaction Go/preflight-credential section after downloading Go modules. The script had already passed root/class state preflight, installed-generation binding, exact transaction-helper Git-object materialization, and Go 1.26.3 archive verification. It did NOT print V3_WORKSPACE_CONTROL_CREDENTIAL=PASS, CANARY_AUTHORITY_CREATED, GENERATION_EXCLUSION=BEGIN, a transaction receipt, or a canary run ID. Therefore no ACTIVATE_ONE_V3_CANARY authority was consumed, no v2 controller was quiesced, no v3 class controller was activated, and no canary workflow was dispatched. First action in the new executor: inspect scripts/lambda_ci_v3_first_canary_live.sh at 52b82..., diagnose the silent failure around the Go build / ephemeral gh-token credential preflight without blindly rerunning it, then produce a corrected exact-head-green operator and continue only the workspace-control-control-small-v1 bounded canary.

## Remaining work

- Diagnose and fix the pre-transaction silent exit in scripts/lambda_ci_v3_first_canary_live.sh at operator head 52b82bcb1c1fe8f9304be6c4e7cd7737b5c88227. The observed last output is Go module downloads from the v3-canary-preflight build; no V3_WORKSPACE_CONTROL_CREDENTIAL=PASS followed.
- Before any retry, verify live state: v3 reconciler/provisioner active and non-enabled, all nine v3 class controllers inactive, Research GPU legacy controller inactive, no ACTIVATE_ONE_V3_CANARY consumption marker/transaction receipt/canary run from the failed attempts, and clean or intentionally recreated workspace-control v3 credential staging.
- Make the corrected Input #3 operator fail loudly around the Go preflight-helper build and ephemeral gh-token credential staging; validate the exact new head in Workspace Control CI before Lambda retry.
- Complete exactly one workspace-control-control-small-v1 generation-exclusion canary: create one-shot authority, prove v2 drain, activate only target v3 controller, dispatch only the owner-only canary, require terminal success, prove v3 execution/resource drain, then restore exact captured v2 prestate.
- After accepted first canary, advance additional public-network classes only in frozen migration order under separately accepted live authority.
- Keep all Research GPU-derived classes NO_BY_DEFAULT until separate containment-recovery authority; keep Research Engine PR #283 proposal-only until separate default-branch producer cutover authority.
- Only after accepted class canaries may old scale-set drain/retirement and broader production activation be separately authorized.

## Blockers / gates

- Input #3 operator head 52b82bcb1c1fe8f9304be6c4e7cd7737b5c88227 exits silently during the pre-transaction Go/preflight-credential section after Go module downloads. Diagnose the exact command failure before another live retry.
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
