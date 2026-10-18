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
- Remote checkpoint: d537027e51adb46652d140cd259904a361ad71ee
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: e5a9b4c361ac790562fac5cf2f35f5a54f2bf58d
- Remote verified: true

## Next safe action

Install exact workspace-control implementation SHA d537027e51adb46652d140cd259904a361ad71ee on Lambda with the accepted P5 bootstrap, but do not activate model-eval-dual-gpu. Verify installed executable blobs and dormant policy/manifest identities: project manifest 1a6fe41dcba1ec868a9fa64984df7b788d51bbf8, workload policy 416981fcc5429dd5b5a57440503b17bad9d38e53, systemd profiles 7461bb658c3c587570ef5fe0353ba89c9c5cf3d1. Run root-authored host acceptance without model weights: exact UUID->device/minor resolver, wrong/missing/reversed UUID denial, generic gpu-heavy dispatch denial, selected-GPU idle proof, controlled unrelated-busy denial, controlled project-owned-residue RuntimeCleanupError classification with cleanup, and an exact two-GPU systemd CUDA/NCCL all-reduce canary under DevicePolicy=closed, both exact device ACLs, UUID-ordered CUDA_VISIBLE_DEVICES, ProtectProc=invisible/ProcSubset=all, AF_NETLINK plus loopback-only distributed bootstrap, and existing private-network denies. Require zero process/GPU residue, no lane quarantine, and healthy controllers afterward. Do not run Qwen or activate dual admission yet; dual timeout/cancel and CUDA-OOM gates remain before activation.

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
