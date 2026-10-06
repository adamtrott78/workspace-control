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
- Remote checkpoint: 4d9e48d4a48b5f0f89bffde15639904bff178168
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 12dd0f2f9510f682f0b62fe8fdc9a63494da8d6d
- Remote verified: true

## Next safe action

Create a same-repository non-scientific research-engine candidate PR whose exact head SHA is safe to execute on the accepted P5 CPU/gpu-small lanes. Trigger the existing trusted /lambda-ci-p5 <exact_sha> and /lambda-ci-p5-gpu <exact_sha> issue_comment workflows on that PR. Require both GitHub jobs and root execution receipts to prove admission-v2 identity, exact trusted workflow blob/candidate binding, accepted cpu-test/gpu-small profile isolation, terminal status, and residue-free cleanup. If either lane fails, diagnose from GitHub/controller/provisioner evidence without widening authority. Do not enable model-acquire, cache-promote, model-eval-single-gpu, gpu-heavy, production routing, or scientific-state mutation in this stage.

## Remaining work

- Run live non-scientific admission-v2 acceptance through same-repository research-engine candidate PR using trusted /lambda-ci-p5 <exact_sha> and /lambda-ci-p5-gpu <exact_sha>, then validate root receipts and residue-free cleanup.
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
