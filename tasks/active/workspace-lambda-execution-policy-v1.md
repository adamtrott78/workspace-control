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
- Remote checkpoint: 5557b54a147ee64cc486af2d1709bd50b67459ac
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 12dd0f2f9510f682f0b62fe8fdc9a63494da8d6d
- Remote verified: true

## Next safe action

Trigger one NEW trusted /lambda-ci-p5 <exact_sha> issue-comment run on the open same-repository non-scientific research-engine candidate f5ba8278d7dfa22e63623ddf51896a6dec002813. Require that fresh CPU run to leave queued state, execute only under the accepted cpu-test profile, complete successfully, and produce/retain root admission plus residue-free cleanup evidence. Only after CPU PASS, trigger one NEW /lambda-ci-p5-gpu <exact_sha> run on the same candidate and require accepted gpu-small profile binding, the pinned single-A4500 UUID, bounded CUDA proof, terminal receipt, and residue-free cleanup. Do not count canceled runs 37533291290 or 37534646664 as acceptance evidence. Do not enable model-scale classes or gpu-heavy.

## Remaining work

- Run fresh non-scientific admission-v2 CPU and gpu-small acceptance against the live 526e020a4d4ef429ceeac173b9f51fbd75912d99 controller and validate root receipts plus residue-free cleanup.
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
