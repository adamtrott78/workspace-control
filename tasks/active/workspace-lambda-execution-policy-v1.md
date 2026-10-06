<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-execution-policy-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-execution-policy-v1
- Title: Workspace Lambda Execution Policy and Model Workload Governance v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, implement, and adversarially validate a fail-closed workload admission, trusted model/dependency cache, resource-governance, and execution-evidence layer on top of the accepted Lambda P5 CPU and gpu-small autonomous runner substrate so ChatGPT/GitHub-driven work can safely execute pinned model-scale workloads without granting candidate workflow code the ability to invent capabilities, persist mutable cross-job state, access production/scientific state, or widen host authority.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: e77af13b3ad43b4252031d27f72773cfd8f232dd
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 577764f4db10e4f4f894b1613518c358c6da7b95
- Remote verified: true

## Next safe action

Begin admission_manifest_and_enforcement from canonical workspace-control e77af13b3ad43b4252031d27f72773cfd8f232dd. Hydrate the accepted P5 controller/provisioner request protocol and implement root-owned validation against architecture/lambda-ci-workload-policy.v1.json plus the versioned admission and execution-receipt schemas: exact project/trusted-workflow/candidate-SHA binding, declared workload/profile/model/runtime/resource/capability binding, atomic single-use admission consumption, stale/replay/kill-switch rejection, and receipt identity binding. Preserve existing cpu-test/gpu-small authority, keep model-acquire/cache-promote/model-eval-single-gpu non-live until their enforcement gates pass, keep gpu-heavy denied, and do not mutate production research routing or run a model-scale workload in this stage.

## Remaining work

- Implement root-owned admission enforcement without broadening the accepted P5 controller/provisioner authority.
- Implement trusted acquisition/quarantine/promotion and read-only content-addressed model/runtime cache semantics.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
