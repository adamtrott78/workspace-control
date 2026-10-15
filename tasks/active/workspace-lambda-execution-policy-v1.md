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

Audit the accepted trusted-cache manager and promoted-object verification path, then run only the bounded root-authored cache poisoning and incomplete-snapshot rejection acceptance required by adversarial_recovery_and_resource_validation. Use disposable quarantine/test objects or copied metadata; do not mutate the accepted promoted Qwen model object, promoted runtime object, expanded runtime, or live production/scientific state. Prove that content/descriptor tampering and an incomplete snapshot fail closed before candidate/model execution, that no poisoned object can be promoted or verified as trusted, and that accepted trusted objects remain byte/identity unchanged afterward. No model weights may be loaded and no inference may run. After PASS, checkpoint adversarial_recovery_and_resource_validation as complete and proceed to the first offline pinned Qwen3.5-4B gpu-small model pilot.

## Remaining work

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
