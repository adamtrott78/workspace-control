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
- Remote checkpoint: 166b42763d20c465c7f136efc6a97191362431fb
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: b345091924bf175777ac52c5549b10c387cbdf14
- Remote verified: true

## Next safe action

Install exact workspace-control SHA 166b42763d20c465c7f136efc6a97191362431fb on Lambda using the accepted P5 bootstrap. This is an identity-only repin: verify unchanged bootstrap fbd33b8d73c8a6e94dbe13b29e656e26973c814b, admission 19e10ded65eea4924673bf7a9efa3c7f27767c4d, provisioner f8a0e1ddd6a770d46cb6c2fb017f58e3baa86260, provisioner-service 74e7838e44eebd3a73dde620a61d3b052d78e466, runtime 18fccff990b5ec46e538e160df4f25879721cfa8, trusted-cache manager a97cb0be0e8f1f53504b33aed7c31a5aa6cb7807, corrected project manifest 693aea12063394f22c11ce80096f153093d17657, and workload policy 929a600f7e9dbe45e407ac0ea07b5cfa58b59d0d. Require trusted-cache manager root:root mode 555; trusted model-eval workflow blob 9d2f845f4182d0610692376ac3d812112f421172; research-engine baseline b345091924bf175777ac52c5549b10c387cbdf14; model-eval ProtectProc=invisible + ProcSubset=all; ordinary gpu-small ProtectProc=invisible + ProcSubset=pid; promoted Qwen object/expanded runtime verify PASS; all three control-plane services active with NRestarts=0; zero project/GPU residue/quarantine. Confirm candidate PR #118 remains open at exact head dd8d15bdb61509f76e92a47cab2d937a8d45069b. Only then issue exactly one next /lambda-ci-qwen35-pilot dd8d15bdb61509f76e92a47cab2d937a8d45069b comment. gpu-heavy remains activation-gated until single-GPU pilot VALIDATED.

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
