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
- Remote checkpoint: b1217e296ca939e344b619db474822f9ce611b82
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: ba3df4238902a382df9e807889ff048b98750012
- Remote verified: true

## Next safe action

Begin dual-GPU implementation while live gpu-heavy remains DENY. First capture the exact host inventory for both RTX A4500 devices (index, UUID, name, memory, PCI bus ID) so the second GPU can be bound by UUID rather than index. In parallel, implement non-live two-GPU support on a workspace-control branch: define a dual-GPU resource class and separate model-eval-dual-gpu workload/claim; generalize root GPU assignment/DeviceAllow/CUDA_VISIBLE_DEVICES/receipt code from one exact UUID to an exact ordered/set-validated two-UUID allocation; preserve existing gpu-small/model-eval-single-gpu behavior byte-for-byte semantically; keep generic gpu-heavy model_binding forbidden and admission disabled until acceptance. Require FULL_INTEGRATION before any host install. No single-GPU pilot rerun is authorized.

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
