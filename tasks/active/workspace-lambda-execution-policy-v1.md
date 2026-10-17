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

Validate and merge workspace-control branch qwen35-procfs-model-runtime-fix. The runtime change must apply ProcSubset=all only when an exact promoted model binding is present, retain ProtectProc=invisible for process privacy, and leave ordinary gpu-small at ProcSubset=pid. Require Python regression, pinned Go/controller validation, and FULL_INTEGRATION because scripts/lambda_ci_runtime.py changes; exact new runtime blob on the branch is 18fccff990b5ec46e538e160df4f25879721cfa8. After merge, reinstall the exact merged workspace-control SHA on Lambda using the accepted P5 bootstrap, verify the installed runtime blob plus unchanged admission/provisioner/service/trusted-cache/model/runtime/workflow identities, prove model-eval systemd command has ProtectProc=invisible + ProcSubset=all while ordinary gpu-small remains ProtectProc=invisible + ProcSubset=pid, reverify promoted Qwen object/expanded runtime/control-plane/zero residue, and only then issue one next /lambda-ci-qwen35-pilot comment on unchanged candidate PR #118 head dd8d15bdb61509f76e92a47cab2d937a8d45069b. If that run fails, diagnose from receipt before any further retry. gpu-heavy activation remains gated until single-GPU pilot VALIDATED.

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
