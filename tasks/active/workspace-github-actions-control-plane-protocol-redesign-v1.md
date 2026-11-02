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
- Remote checkpoint: 40d2004ab58b7027a604f4462ef8f06b1cf7c92a
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

Complete this task/handoff sync and freeze the resulting exact branch head. From a fresh clean checkout at that exact final head, run only `bash scripts/lambda_ci_v3_controller_refresh_live.sh`. The refresh must prove roots active+boot-disabled, all nine v3 class controllers non-active+boot-disabled, Research GPU legacy containment, fully rolled-back migration history, and shared reconciler verification of the effective installed generation before replacing only /opt/workspace-ci/v3/controller/lambda-ci-controller-v3. Independently verify the root-owned V3_INACTIVE_CONTROLLER_BINARY_OVERRIDE receipt and unchanged runtime/reconciler bindings. Only then retry `bash scripts/lambda_ci_v3_production_cutover_live.sh` from the same exact head with a fresh production authority.

## Remaining work

- Validate this task/handoff sync and freeze the final exact controller-refresh/cutover source head.
- Run scripts/lambda_ci_v3_controller_refresh_live.sh from that exact head; independently verify controller override provenance, binary digest, roots, all-class inactivity/boot state, restored v2 lanes, and Research GPU containment.
- Retry the production generation cutover from the same exact head. Production prepare must reject any nonterminal durable v3 ledger before authority; terminal prior-generation history is inert.
- Independently verify all three real production jobs, exact workflow blobs, selected v3 active+enabled state, non-selected v3 inactive+disabled state, all v2 inactive+disabled after commit, Research CPU separately gated, Research GPU contained, and production transaction/override receipts.
- Preserve retired accepted v2 scale sets/bytes/config/state through the rollback window; physical legacy cleanup remains a later separately validated action.
- Immediately resume workspace-semantic-execution-migration-v1 umbrella work once the v3/v2 infrastructure gate is accepted.

## Blockers / gates

- The validated controller binary and refresh-verifier repair still require one bounded root controller-only refresh from the final exact task-sync head. The prior refresh attempt failed before mutation and does not need rollback.
- After that controller refresh is independently verified, production cutover attempt #2 requires a fresh one-shot CUTOVER_V3_PRODUCTION_GENERATION authority through the validated live operator; no prior production authority may be reused.
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
