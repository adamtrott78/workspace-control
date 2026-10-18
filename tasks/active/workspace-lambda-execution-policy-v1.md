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
- Remote checkpoint: 56e35d53eb086ab9ec8a5be49e070376b9baa5a3
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: e5a9b4c361ac790562fac5cf2f35f5a54f2bf58d
- Remote verified: true

## Next safe action

Install exact workspace-control SHA 56e35d53eb086ab9ec8a5be49e070376b9baa5a3 on Lambda. Verify exact installed runtime d8454f082c822a4ef4e347e3e66714bcbc324f1f and trusted dual probes root:root 0555 with blobs 3d420d39924b4cd932b70c7303a80eaf8c098c36 and 8330b3621f80dbe78e413234deec4b4f433e2ce7; dormant manifest/policy/profiles must remain 1a6fe41dcba1ec868a9fa64984df7b788d51bbf8 / 416981fcc5429dd5b5a57440503b17bad9d38e53 / 7461bb658c3c587570ef5fe0353ba89c9c5cf3d1, with model-eval-dual-gpu not live and generic gpu-heavy denied. Then execute two root-authored production launch_gpu_runner canaries without admission/Qwen: (1) dual timeout probe with gpu-heavy/model-eval-dual-gpu exact UUID pair and short RuntimeMaxSec, require RuntimeTimeoutError plus receipt TIMED_OUT, timed_out=true, systemd Result=timeout, both CPU/GPU cleanup, workspaces destroyed, runtime/model postverify, non-retryable; (2) dual CUDA OOM probe with same exact authority, require RuntimeCudaOomError plus CUDA_OOM receipt, cuda_oom=true, trusted exit-86 evidence, both CPU/GPU cleanup, workspaces destroyed, runtime/model postverify, non-retryable. Finish with both GPUs idle, no project processes/quarantine, controllers healthy. Do not enable dual admission or run Qwen until both PASS.

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
