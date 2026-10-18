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
- Remote checkpoint: e5a9b4c361ac790562fac5cf2f35f5a54f2bf58d
- Remote verified: true

## Next safe action

Validate workspace-control branch dual-gpu-bounded-authority with FULL_INTEGRATION. The branch must remain non-live: canonical admission_v2.live_enabled_workload_classes stays [cpu-test,gpu-small,model-eval-single-gpu]; model-eval-dual-gpu policy_decision stays DESIGNED_NOT_LIVE with admission_enabled_after_enforcement=false; generic gpu-heavy remains DENY. Require controller claim/command exactness, exact resource class model_eval_dual_gpu_v1 bound to UUID order [GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea,GPU-cfed3394-a935-63aa-9325-c4cae7b568b6], root service gpu-heavy lane limited to model-eval-dual-gpu, runtime launcher rejection of all other gpu-heavy workloads, correct UUID-to-device mapping /dev/nvidia1,/dev/nvidia0, plural receipt identity, schemas/tests, and research-engine workflow blob a961158615269797837e036fb4cc4a3358f60189 pinned to research main e5a9b4c361ac790562fac5cf2f35f5a54f2bf58d. If FULL_INTEGRATION passes, merge but do not activate live admission. Then install the exact merged non-live code on Lambda and run root-authored two-GPU host acceptance canaries before any policy activation.

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
