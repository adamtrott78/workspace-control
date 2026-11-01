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
- Remote checkpoint: 3e8a231483413ba3a16d405ba61b55d0ab9ff3aa
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

INPUT #3 IS ACCEPTED. The initial live v3 proof for workspace-control-control-small-v1 succeeded end-to-end at exact controller/source head 3e8a231483413ba3a16d405ba61b55d0ab9ff3aa. Do NOT repeat Input #1, Input #2, or the workspace-control first canary. The accepted canary run is 41264356722 and the operator proved exact rollback, root services still active, all v3 class controllers inactive, and Research GPU containment preserved. Next migration-order target is padataset-cpu-public-v1. Before any live mutation, prepare and validate a separate one-class canary package/authority for that target, preserving generation exclusion, exact rollback, and all Research GPU-derived NO_BY_DEFAULT containment.

## Remaining work

- Prepare the migration-order #2 canary for padataset-cpu-public-v1 under a new separately validated one-shot ACTIVATE_ONE_V3_CANARY authority. Do not reuse the consumed workspace-control authority or transaction.
- Execute padataset-cpu-public-v1 canary only after exact repository validation and live preflight prove all v2/v3 transients drained, the existing v3 root services healthy, and every non-target v3 class inactive.
- After PADataset CPU acceptance, prepare migration-order #3 padataset-gpu-single-public-v1 canary with the same generation-exclusion/rollback discipline.
- Keep research-cpu-public-v1 inactive unless separately authorized; keep all Research GPU-derived classes NO_BY_DEFAULT until separate containment-recovery authority.
- Keep Research Engine PR #283 proposal-only until separate default-branch producer cutover authority.

## Blockers / gates

- No blocker remains for the accepted workspace-control first canary; it is complete and must not be repeated.
- Further live migration requires a new separately bound one-shot canary authority per class, beginning with padataset-cpu-public-v1.
- Research CPU activation remains separately gated.
- All Research GPU-derived runner classes remain inherited-contained and NO_BY_DEFAULT.
- Research Engine PR #283 remains draft/proposal-only; no default-branch producer cutover is authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
