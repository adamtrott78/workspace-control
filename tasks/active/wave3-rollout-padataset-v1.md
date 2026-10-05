<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/wave3-rollout-padataset-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: wave3-rollout-padataset-v1
- Title: Wave-3 Rollout — PADataset v1
- Status: BLOCKED_EVIDENCE
- Capsule schema: v2

## Goal

Adopt the frozen Wave-3 scope-adherence and, where applicable, heavyweight-runtime certification/recovery contract into the active PADataset control-plane lineage without changing PADataset scientific/RF truth, experiment semantics, or project-owned artifact behavior.

## Repositories

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 1295477546c802029d7c52755beeacdef31b5346
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: control-plane-v2-integration
- Remote checkpoint: d6f6a7281f20d250423abd35ee5991841677e27d
- Remote verified: true

## Next safe action

Start from https://github.com/adamtrott78/workspace-control and the normal root route. Read tasks/active/workspace-control-throughput-ci-efficiency-v1.json first. Do not mutate PADataset while the parent Wave-3 freeze/rollout gate remains unsatisfied. If and only if the parent capsule durably authorizes cross-repository rollout, re-verify PADataset branch control-plane-v2-integration against recorded checkpoint d6f6a7281f20d250423abd35ee5991841677e27d; if it advanced, update this capsule JSON and regenerate its Markdown before any target mutation. Then enter lineage_revalidation and follow the frozen shared Wave-3 contracts using the smallest project-local binding. If the parent gate is still closed, make no target-repository changes and stop.

## Remaining work

- Release the freeze gate only from durable parent-task evidence; do not infer readiness from conversation state.
- Re-verify PADataset:control-plane-v2-integration and reconcile any advancement from d6f6a7281f20d250423abd35ee5991841677e27d.
- Adopt root scope routing plus a thin project-local scope adapter without vendoring generic control-plane logic.
- Assess heavyweight runtime-certification applicability and either adopt bounded project-local integration or record a validated SKIPPED result.
- Run project-appropriate validation, promote the exact reviewed head, synchronize this task capsule/derived handoff, and CHECKPOINT_AND_STOP.

## Blockers / gates

- Wave-3 rollout is gated until parent task workspace-control-throughput-ci-efficiency-v1 durably records freeze readiness after the remaining R2/C3 field evidence is satisfied.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/wave3-rollout-padataset-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
