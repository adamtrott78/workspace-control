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
- Remote checkpoint: 602ff543a122038870598915f669d9f9bd5a9f6a
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

First complete task/handoff sync validation for this production-cutover implementation. Then, from a clean checkout at that exact final durable head, execute only the bounded root verifier refresh `sudo /usr/bin/python3 scripts/lambda_ci_v3_reconciler_live_update_v2.py --expected-head <FINAL_DURABLE_HEAD>`. Independently verify the new reconciler override, roots, all-class inactivity, and Research GPU containment. Only after that proof, execute `bash scripts/lambda_ci_v3_production_cutover_live.sh` from the same exact head. The operator must remain the sole creator/consumer of a fresh CUTOVER_V3_PRODUCTION_GENERATION authority and must either produce V3_PRODUCTION_CUTOVER_ACCEPTED=PASS or fail closed through workflow restoration plus v3-isolated rollback.

## Remaining work

- Validate this task/handoff sync and freeze the final exact durable production-cutover source head.
- Execute the reconciler-only live verifier refresh at that exact head; independently prove installed reconciler bytes/override, root health, all nine v3 class controllers inactive+boot-disabled, and Research GPU containment.
- Execute the validated production cutover operator at the same exact head: quiesce all v2 controllers, retarget exactly three trusted production workflows, activate exactly the three accepted v3 classes, validate one real production job per accepted class, prove clean transient/resource state, and commit.
- Independently verify post-cutover workflow blobs, selected v3 controller active+enabled state, non-selected v3 inactive+disabled state, all v2 controllers inactive+disabled, Research CPU separately gated, Research GPU contained, and production override/transaction receipts.
- Preserve retired accepted v2 scale sets/bytes/config/state through the rollback window; perform physical legacy cleanup only as a later separately validated step.
- Immediately resume workspace-semantic-execution-migration-v1 umbrella work after the v3/v2 infrastructure gate is accepted.

## Blockers / gates

- The live host still needs the newly validated reconciler verifier installed through scripts/lambda_ci_v3_reconciler_live_update_v2.py at the final exact task-sync head before any production cutover authority can be created. The updater is reconciler-only and grants no cutover authority.
- After that verifier refresh is independently attested, the single production cutover still requires the validated operator/root transaction; current Workspace Shell authority cannot mint the needed root approval or execute generic root mutations.
- Research CPU is separately gated and must remain inactive after successful v3 cutover; all Research GPU-derived classes remain inherited-contained and NO_BY_DEFAULT.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
