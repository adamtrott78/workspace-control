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
- Remote checkpoint: 467b8fb136d71448f7b44788200afca6c9673e32
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 6165556086b73d2076f205f11ec7b988150f23dd
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d214b20471aac348bd28802596b92f81ee146b76
- Remote verified: true

## Next safe action

Finish the existing production-cutover rollback first. The operator terminal that launched scripts/lambda_ci_v3_production_cutover_live.sh must be interrupted once if it is still running so its existing EXIT rollback trap can complete. Independently require: production workflows restored to their old blobs, workspace-control-control-small-v1 inactive/dead, all other v3 class controllers inactive, v2 workspace-control/PADataset CPU/PADataset GPU/Research CPU restored to their exact pre-cutover active+enabled states, Research GPU inactive+disabled, roots healthy, and transaction c4c11247-0883-4eab-91fd-3b5306b23de6 phase ROLLED_BACK_LEGACY_RESTORED. Only then freeze the final task-sync head, install the validated controller binary with scripts/lambda_ci_v3_controller_refresh_live.sh, verify its active root-owned controller override, and retry production cutover from that same exact head.

## Remaining work

- Complete and independently attest rollback of production cutover attempt #1; no new authority or live refresh while the transaction is nonterminal.
- Task/handoff-sync the validated durable-ledger generation fix and freeze the final exact source head.
- Install the controller-only refresh from that exact head using scripts/lambda_ci_v3_controller_refresh_live.sh; verify all v3 class controllers remained inactive during refresh and Research GPU containment remained intact.
- Retry the single production generation cutover. Terminal historical ledger records may be ignored; any nonterminal ledger record must block before authority. Validate one real production job per accepted class and prove clean transient/resource state before commit.
- Independently verify post-cutover workflow blobs, selected v3 controller active+enabled state, non-selected v3 inactive+disabled state, all v2 controllers inactive+disabled, Research CPU separately gated, Research GPU contained, and production override/transaction receipts.
- Preserve retired accepted v2 scale sets/bytes/config/state through the rollback window; perform physical legacy cleanup only later.
- Immediately resume workspace-semantic-execution-migration-v1 umbrella work after the v3/v2 infrastructure gate is accepted.

## Blockers / gates

- Production cutover attempt #1 is still in a partial rollback boundary. The queued validation run is cancelled and old workflow blobs are restored, but the existing root transaction has not yet proven V3_PRODUCTION_ROLLBACK=PASS / ROLLED_BACK_LEGACY_RESTORED. Do not retry cutover or refresh the controller until that transaction is terminal and all accepted v3 class controllers are inactive.
- After rollback is terminal, the validated controller-only fix at the final task-sync head must be installed with scripts/lambda_ci_v3_controller_refresh_live.sh while all v3 class controllers are inactive. Current Workspace Shell cannot perform this root mutation.
- Research CPU remains separately gated; all Research GPU-derived classes remain inherited-contained and NO_BY_DEFAULT.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
