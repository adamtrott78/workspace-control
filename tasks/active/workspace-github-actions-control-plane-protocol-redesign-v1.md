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
- Remote checkpoint: 56e5976597b0d1523ead6a11cdfe6f8a9d23dda0
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

All currently authorized active-class canaries are accepted. Implement and repository-validate the single controlled production generation cutover from architecture/lambda-ci-v3-migration-plan.v1.json for exactly workspace-control-control-small-v1, padataset-cpu-public-v1 and padataset-gpu-single-public-v1, while keeping Research CPU inactive and every Research GPU-derived class inherited-contained. The cutover must be transactional and fail closed: freeze exact v3 source/catalog/deployment overlay, prove no in-progress migration transaction, drain/quiesce all v2 project controllers and legacy/v3 transient work, atomically bind exact trusted production workflow retargets plus pins/projections, start only the three accepted v3 class controllers, run exact production validation, prove clean ledgers/resources, then move corresponding v2 controllers/scale sets DRAINING -> RETIRED while preserving rollback bytes/state. Do not execute live cutover until the repository implementation and exact operator/root authority path are separately validated.

## Remaining work

- Implement the repository-only production generation cutover transaction/operator and exhaustive rollback tests for exactly the accepted active classes: workspace-control-control-small-v1, padataset-cpu-public-v1, and padataset-gpu-single-public-v1.
- Validate exact production workflow retarget bytes/pins/projections and a one-shot live cutover authority contract; preserve Research CPU inactive and all Research GPU-derived classes inherited-contained.
- Execute the single controlled production generation cutover through the operator/root authority boundary, validate one exact production job per accepted class, and prove v3 controller/runner/resource ledgers clean.
- Move corresponding v2 controllers/scale sets through DRAINING -> RETIRED only after accepted v3 production proof, preserving rollback bytes/config/state for the rollback window; perform later legacy cleanup separately.
- Immediately resume workspace-semantic-execution-migration-v1 umbrella work after the v3/v2 infrastructure gate is accepted.

## Blockers / gates

- Production v3 generation cutover/v2 retirement has not yet been executed; it requires a separately reviewed and validated live cutover transaction bound to exact accepted classes, workflow bytes, deployment generation and rollback state.
- Current Workspace Shell authority still cannot mint live root/cutover approvals or provide generic root execution; no authority may be inferred from this task state.
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
