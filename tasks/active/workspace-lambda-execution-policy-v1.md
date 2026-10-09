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
- Remote checkpoint: effc5b2f39fe897f4b9dc9fe6767d2002ee81cdb
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: fa0ff6f1a4a46fd0295e45df401aa8361d220c86
- Remote verified: true

## Next safe action

Audit the currently installed concurrency/admission/runtime controls for cpu-test and gpu-small and the root-owned project concurrency ceiling, then run only the bounded CPU/GPU contention and concurrency acceptance required by adversarial_recovery_and_resource_validation. Preserve the accepted cpu-test/gpu-small capability boundaries, exact single-GPU UUID binding, immutable expanded-runtime binding, cleanup/quarantine semantics, and no-model/no-inference constraint. Do not enable gpu-heavy or dual-GPU and do not rerun already accepted failure-envelope gates solely for reassurance. Require compact evidence that overlapping or competing CPU/GPU requests are either safely serialized/rejected according to root policy or execute only within the explicitly accepted concurrency ceiling, with no cross-request workspace/cache/process/GPU leakage and all lanes healthy afterward. After PASS, checkpoint concurrency acceptance and proceed to cache poisoning/incomplete-snapshot rejection.

## Remaining work

- Run CPU/GPU contention and concurrency acceptance without expanding cpu-test or gpu-small authority.
- Run cache poisoning and incomplete-snapshot rejection acceptance against the trusted-cache boundary.
- After the adversarial recovery/resource/cache matrix is complete, run the first offline Qwen3.5-4B pinned-model pilot on gpu-small under the already-promoted model/runtime identities.
- Decide separately whether gpu-heavy or dual-GPU should ever be accepted; they remain denied.

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
