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
- Remote checkpoint: 1edb253a1525018aa28652519c56c22edea0fb92
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 89191de6821ed29c4f8494834e7c006e4725d8f9
- Remote verified: true

## Next safe action

Install exact workspace-control SHA 1edb253a1525018aa28652519c56c22edea0fb92 on Lambda using the accepted P5 bootstrap. This is an identity-only repin: bootstrap fbd33b8d73c8a6e94dbe13b29e656e26973c814b, admission 19e10ded65eea4924673bf7a9efa3c7f27767c4d, provisioner f8a0e1ddd6a770d46cb6c2fb017f58e3baa86260, provisioner-service 74e7838e44eebd3a73dde620a61d3b052d78e466, runtime e09aa9d6961615a259c825d436f95adce668441f, and trusted-cache manager a97cb0be0e8f1f53504b33aed7c31a5aa6cb7807 must remain unchanged; only project-manifest blob fe81231bf600cd37fc74dcbfc6ff72f20bfe965b and workload-policy blob b5c0c502003b071e47e3da7724b6cb4b72538fe0 should change. Require trusted-cache manager root:root mode 555, corrected workflow blob fe83ad7d5e5e08335f4ad6e1acccceceaf4cafd5 bound in model-eval-single-gpu, promoted Qwen object and expanded runtime verify PASS, all three control-plane services active with NRestarts=0, and zero project/GPU residue/quarantine. Then verify candidate PR #118 is still open at exact head dd8d15bdb61509f76e92a47cab2d937a8d45069b. Only after that host gate passes, issue exactly one second /lambda-ci-qwen35-pilot dd8d15bdb61509f76e92a47cab2d937a8d45069b comment. Do not create a new candidate SHA or issue another retry if the second attempt fails; diagnose first. gpu-heavy remains activation-gated until the single-GPU pilot is VALIDATED.

## Remaining work

- Run and accept the first offline Qwen3.5-4B pinned-model pilot on gpu-small using one synthetic non-scientific image+text inference.
- After the pilot is accepted, decide separately whether gpu-heavy or dual-GPU should ever be accepted; they remain denied.

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
