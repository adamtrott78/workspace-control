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

Run the two remaining physical failure gates only through scripts/lambda_ci_dual_failure_acceptance.py from exact workspace-control 76c5e1c857f7c1e0d6a7628221821c644f5d6ae9 (blob 750de6cde54c43ed4e8d6cd1afd980bec72bcf75). First verify installed 0f8375a889863c673fb79f76d83c7b94977a9252 executable/config identities and that model-eval-dual-gpu plus generic gpu-heavy remain non-live. Then maintenance-isolate the controllers/provisioner, execute the harness as root against /opt/workspace-ci/provisioner, and require DUAL_TIMEOUT_ACCEPTANCE=PASS followed by DUAL_CUDA_OOM_ACCEPTANCE=PASS and final DUAL_FAILURE_HOST_ACCEPTANCE=PASS. Restore services active NRestarts=0 with zero project CPU/GPU residue. Do not rerun dormant NCCL. Do not merge activation PR #193 or trigger research-engine PR #123 until this host acceptance PASS is checkpointed.

## Remaining work

- After exact runtime restoration, reverify installed workspace-control implementation 0f8375a889863c673fb79f76d83c7b94977a9252 and immutable dual timeout/CUDA-OOM probe identities without reinstalling or rerunning already-accepted gates unless identity has actually drifted.
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
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
