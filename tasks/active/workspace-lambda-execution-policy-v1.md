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
- Remote checkpoint: 9eeb86be492761875bcd62703199d0fb8e8c986c
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: b345091924bf175777ac52c5549b10c387cbdf14
- Remote verified: true

## Next safe action

Validate and merge workspace-control branch qwen35-spawn-workflow-repin. This is an identity-only repin to research-engine main b345091924bf175777ac52c5549b10c387cbdf14 / trusted Qwen pilot workflow blob 9d2f845f4182d0610692376ac3d812112f421172, producing project-manifest blob 693aea12063394f22c11ce80096f153093d17657 and workload-policy blob 929a600f7e9dbe45e407ac0ea07b5cfa58b59d0d. Executable workspace-control P5 code must remain unchanged from accepted 9eeb86be492761875bcd62703199d0fb8e8c986c, including runtime blob 18fccff990b5ec46e538e160df4f25879721cfa8. After canonical validation/merge, reinstall only the exact merged workspace-control SHA on Lambda using the accepted P5 bootstrap, verify the new manifest/policy/workflow pin plus unchanged bootstrap/admission/provisioner/service/runtime/trusted-cache/model/runtime/control-plane identities and zero residue. Confirm PR #118 remains open at exact head dd8d15bdb61509f76e92a47cab2d937a8d45069b. Only then issue exactly one next /lambda-ci-qwen35-pilot comment. If that attempt fails, diagnose from the uploaded receipt before any further retry. gpu-heavy activation remains gated until single-GPU pilot VALIDATED.

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
