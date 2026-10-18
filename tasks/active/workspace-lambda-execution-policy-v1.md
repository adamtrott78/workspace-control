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
- Remote checkpoint: cab67e1f5afa231b9cde59adb808ffe98cd1c8cf
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: ba3df4238902a382df9e807889ff048b98750012
- Remote verified: true

## Next safe action

Implement the exact dual-GPU authority using UUID order [GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea, GPU-cfed3394-a935-63aa-9325-c4cae7b568b6]. Create a separate research-engine trusted workflow for workload model-eval-dual-gpu using command /lambda-ci-qwen35-dual-pilot and tensor_parallel_size=2, recording per-GPU memory/use and requiring both UUIDs. In workspace-control, add controller recognition for that exact workload/command, a DESIGNED_NOT_LIVE model_eval_dual_gpu_v1 resource class bound to execution_profile gpu-heavy and the two exact UUIDs, a non-live manifest route with model binding qwen3.5-4b and the same immutable expanded runtime under a gpu-heavy binding, and root runtime support that accepts gpu-heavy only when workload_class=model-eval-dual-gpu with the exact UUID pair. Generic gpu-heavy remains DENY/model-forbidden and model-eval-dual-gpu remains not live-enabled until host acceptance gates pass. Require FULL_INTEGRATION before host install.

## Remaining work

- Bind the exact second RTX A4500 UUID and freeze the two-GPU hardware identity set; do not use GPU indices alone as authority.
- Implement dual-GPU admission/provisioner/runtime support behind a new exact resource class while keeping current gpu-heavy DENY live policy unchanged.
- Keep generic gpu-heavy model access forbidden; introduce a separate model-eval-dual-gpu authority for promoted-model tensor-parallel work.
- Validate two-device allocation, wrong/missing UUID denial, preexisting residue denial/quarantine, timeout/cancel cleanup, CUDA OOM behavior, runtime/model identity failure, and exact pre/post receipts.
- Run one bounded non-scientific Qwen tensor_parallel_size=2 image+text canary proving both A4500s are actually used and fully cleaned up.
- Only after all dual-GPU acceptance gates pass, decide whether to activate bounded gpu-heavy/model-eval-dual-gpu authority.

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
