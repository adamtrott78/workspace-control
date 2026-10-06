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
- Remote checkpoint: 12f9d9e3a59f042bcf832dfe89a3b389b92f21ce
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 577764f4db10e4f4f894b1613518c358c6da7b95
- Remote verified: true

## Next safe action

Start from architecture/lambda-ci-execution-policy-hydration.v1.md and the accepted parent baseline. Complete the policy_contract_and_hydration stage by designing a versioned workload-class taxonomy plus root-owned admission manifest/schema and execution-receipt contract. Preserve cpu-test/gpu-small as already accepted capabilities, keep gpu-heavy denied, keep candidate jobs unable to promote trusted cache content, and keep model-eval offline/no-registry-credential by default. Do not mutate the live Lambda or run a model-scale workload until the policy contract has passed workspace-control validation.

## Remaining work

- Finish and validate the workload-class taxonomy, admission schema, exception model, and execution-receipt contract.
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
