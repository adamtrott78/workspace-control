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
- Remote checkpoint: 0f8375a889863c673fb79f76d83c7b94977a9252
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: e5a9b4c361ac790562fac5cf2f35f5a54f2bf58d
- Remote verified: true

## Next safe action

Run the two root-authored dual failure gates on Lambda; this is the only remaining prerequisite before activation. Use exact workspace-control implementation 0f8375a889863c673fb79f76d83c7b94977a9252. Verify installed blobs: bootstrap 1f1203a17567ff95302938afd9d8060723407d31, runtime e7001b7f5e7b69c35da9b325ed9b8e6dc1cc4d0b, dual timeout probe 3d420d39924b4cd932b70c7303a80eaf8c098c36, dual CUDA-OOM probe 8330b3621f80dbe78e413234deec4b4f433e2ce7, dormant manifest 1a6fe41dcba1ec868a9fa64984df7b788d51bbf8, dormant policy 416981fcc5429dd5b5a57440503b17bad9d38e53, profiles 7461bb658c3c587570ef5fe0353ba89c9c5cf3d1; probes root:root 0555. Keep model-eval-dual-gpu not live and generic gpu-heavy DENY during these gates. Build root-authored gpu-heavy/model-eval-dual-gpu launch specs from installed manifest/profiles/pins with exact UUID order [GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea,GPU-cfed3394-a935-63aa-9325-c4cae7b568b6], exact promoted Qwen binding and gpu-heavy expanded runtime, no admission, and immutable trusted_failure_probe. Timeout probe kind dual_gpu_timeout_acceptance_v1 must run under a root-authored ~5s RuntimeMaxSec and raise RuntimeTimeoutError; require receipt terminal_status=TIMED_OUT, timed_out=true, systemd Result=timeout, automatic_retry_eligible=false, project_uid_process_cleanup=true, project_uid_gpu_process_cleanup=true, leaked_gpu_processes=[], runner_workspace_destroyed=true, staging_workspace_destroyed=true, expanded_runtime pre/post verified, promoted_model pre/post verified. OOM probe kind dual_gpu_cuda_oom_acceptance_v1 must raise RuntimeCudaOomError; require receipt terminal_status=CUDA_OOM, cuda_oom=true, cuda_oom_evidence.matched=true, expected_exit_code=86, systemd result=exit-code / ExecMainStatus=86, and the same cleanup/postverify guarantees. Finish both exact GPUs idle, no ci-research-engine processes, no cpu-test/gpu-small/gpu-heavy quarantine, controllers active NRestarts=0. Do NOT merge activation PR #193 or trigger PR #123 until both gates PASS. After both PASS: checkpoint receipts; merge #193; install and verify the exact merge; then issue exactly one `/lambda-ci-qwen35-dual-pilot 98f49e957073756411065a315514451fefd08ee6` on PR #123 and follow the single run through workflow receipt plus root cleanup.

## Remaining work

- Install exact workspace-control implementation 0f8375a889863c673fb79f76d83c7b94977a9252 on Lambda and verify the corrected runtime plus immutable root-only dual timeout/CUDA-OOM probe identities.
- Run root-authored dual timeout acceptance and checkpoint the exact P5 root receipt: RuntimeTimeoutError, terminal_status=TIMED_OUT, timed_out=true, systemd Result=timeout, no retry, exact two-UUID binding, runtime/model pre+post verify, CPU/GPU cleanup, workspaces destroyed.
- Run root-authored dual CUDA-OOM acceptance and checkpoint trusted exit-86 evidence: RuntimeCudaOomError, terminal_status=CUDA_OOM, cuda_oom=true, evidence matched on exact probe identity, exact two-UUID binding, runtime/model pre+post verify, CPU/GPU cleanup, workspaces destroyed.
- Only after both root failure gates PASS, merge green activation PR #193 (head a2a002c8b23829c5220f9e64099f9d7a94bfe7b7), install the exact resulting merge SHA, and verify model-eval-dual-gpu alone is live while generic gpu-heavy remains DENY/admission-disabled.
- Issue exactly one `/lambda-ci-qwen35-dual-pilot 98f49e957073756411065a315514451fefd08ee6` comment on research-engine PR #123 and follow only that dedicated run.
- Accept the tensor-parallel pilot only if exact two-UUID binding holds, tensor_parallel_size=2, both UUIDs show >1 GiB peak model memory, exactly one synthetic image+text inference completes, and no scientific input/state, public acquisition, production-routing change, or persistent model server occurs.
- Read the final root-owned dual pilot provisioner receipt and require terminal success, exact workflow/candidate/model/runtime/two-UUID identity, runtime/model postverify, zero project CPU/GPU residue/quarantine, and destroyed job/staging workspaces.
- If all gates pass, mark bounded model-eval-dual-gpu authority VALIDATED. Keep generic gpu-heavy DENY unless a separate generic heavy-workload policy is explicitly designed and accepted.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, synchronized Markdown handoff, exact durable Git/runtime state, and referenced evidence as the complete handoff.
Do not rely on previous conversation state.
Use the connected Workspace Heartbeat plugin according to procedures/progress_heartbeat.md.
Follow the capsule's next_safe_action exactly.
Do not rerun accepted single-GPU or dormant dual NCCL gates.
Do not merge activation or trigger the dual Qwen pilot until both root dual failure gates PASS.
