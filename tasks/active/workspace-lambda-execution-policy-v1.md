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

Install exact workspace-control SHA 0f8375a889863c673fb79f76d83c7b94977a9252 on Lambda using the accepted P5 bootstrap. Verify bootstrap 1f1203a17567ff95302938afd9d8060723407d31, runtime e7001b7f5e7b69c35da9b325ed9b8e6dc1cc4d0b, trusted dual timeout probe 3d420d39924b4cd932b70c7303a80eaf8c098c36, trusted dual CUDA-OOM probe 8330b3621f80dbe78e413234deec4b4f433e2ce7, manifest 1a6fe41dcba1ec868a9fa64984df7b788d51bbf8, policy 416981fcc5429dd5b5a57440503b17bad9d38e53, profiles 7461bb658c3c587570ef5fe0353ba89c9c5cf3d1; both probes must be root:root 0555. Confirm model-eval-dual-gpu remains not live and generic gpu-heavy DENY. Then run two root-authored launch_gpu_runner canaries with exact UUID order [GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea,GPU-cfed3394-a935-63aa-9325-c4cae7b568b6], workload=model-eval-dual-gpu, profile=gpu-heavy, exact promoted Qwen binding and expanded gpu-heavy runtime binding, no admission: (1) dual_gpu_timeout_acceptance_v1 with RuntimeMaxSec about 5s; require RuntimeTimeoutError and root receipt terminal_status=TIMED_OUT, timed_out=true, systemd Result=timeout, automatic_retry_eligible=false, project CPU/GPU cleanup true, leaked_gpu_processes=[], runner/staging destroyed, expanded runtime pre/post verified, promoted model pre/post verified; (2) dual_gpu_cuda_oom_acceptance_v1 with sufficient bounded runtime; require RuntimeCudaOomError and root receipt terminal_status=CUDA_OOM, cuda_oom=true, trusted exit-86 evidence matched, same cleanup/postverify guarantees. Finish both exact GPUs idle, no ci-research-engine processes, no cpu-test/gpu-small/gpu-heavy quarantine, controllers active NRestarts=0. Do NOT merge activation PR #192 or trigger research-engine PR #123 before both PASS. After both PASS: checkpoint receipts; merge #192; install/verify its exact merged manifest+policy while generic gpu-heavy remains DENY; then issue exactly one `/lambda-ci-qwen35-dual-pilot 98f49e957073756411065a315514451fefd08ee6` comment on PR #123 and follow the single dedicated run through tensor_parallel_size=2 receipt + root cleanup. Accept dual model authority only if both UUIDs show >1 GiB model memory, exactly one synthetic image+text inference completes, no scientific/public/production mutation occurs, and terminal/root cleanup are clean.

## Remaining work

- Run root-authored dual timeout acceptance on corrected runtime 0f8375a889863c673fb79f76d83c7b94977a9252 and checkpoint exact receipt/cleanup evidence.
- Run root-authored dual CUDA-OOM acceptance on corrected runtime and checkpoint exact trusted exit-86/receipt/cleanup evidence.
- Only after both failure gates PASS, merge already-green activation PR #192 and install/verify the merged activation identity; generic gpu-heavy must remain denied.
- Trigger exactly one dual Qwen pilot on research-engine PR #123 exact head 98f49e957073756411065a315514451fefd08ee6 and validate tensor_parallel_size=2 uses both exact A4500 UUIDs with >1 GiB model memory each.
- Validate the dual pilot root receipt: exact workflow/candidate/model/runtime/two-UUID binding, terminal success, runtime/model postverify, zero CPU/GPU residue/quarantine, workspaces destroyed, no persistent model server.
- If all pass, mark model-eval-dual-gpu bounded authority VALIDATED; keep generic gpu-heavy denied unless a separate generic heavy-workload policy is explicitly designed and accepted.

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
