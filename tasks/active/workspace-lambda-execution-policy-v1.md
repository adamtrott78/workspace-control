<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-execution-policy-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-execution-policy-v1
- Title: Workspace Lambda Execution Policy and Model Workload Governance v1
- Status: BLOCKED_EVIDENCE
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

Use only the validated read-only helper scripts/runtime_tree_projection.py from exact workspace-control 7d6a7e46557342fdf085e1202970ff200016f547 (blob 0974a03d46c487b32801e88647cba489f363a64d) for the runtime-drift projection gate. Create a disposable fresh reference runtime only as a pathname/type oracle from the already-trusted uv 0.12.23 + trusted 196-wheel bundle; do not treat its bytes or modes as authoritative. Then invoke the helper against the existing drifted canonical runtime and the disposable reference. Require candidate extras exactly +868 files/+172 directories/+0 symlinks, reference-only=0, type-mismatch=0, NON_PYCACHE_EXTRA_COUNT=0, projected files=53583, directories including root=6069, symlinks=4, materialized regular-file bytes=11067818797, projected tree digest=b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63, root ownership retained, and LIVE_RUNTIME_MUTATED=false. If the helper returns REJECT or any invariant differs, stop with zero live mutation. Do not run timeout/OOM or any accepted GPU gate during this step.

## Remaining work

- Restore the accepted expanded Qwen runtime through the incident recovery contract: first obtain an exact non-mutating projection PASS; only then perform a separate reversible quarantine/write-bit repair with immediate authoritative production verification and rollback on any mismatch.
- After exact runtime restoration, reverify installed workspace-control implementation 0f8375a889863c673fb79f76d83c7b94977a9252 and immutable dual timeout/CUDA-OOM probe identities without reinstalling or rerunning already-accepted gates unless identity has actually drifted.
- Run root-authored dual timeout acceptance and checkpoint the exact P5 root receipt: RuntimeTimeoutError, terminal_status=TIMED_OUT, timed_out=true, systemd Result=timeout, no retry, exact two-UUID binding, runtime/model pre+post verify, CPU/GPU cleanup, workspaces destroyed.
- Run root-authored dual CUDA-OOM acceptance and checkpoint trusted exit-86 evidence: RuntimeCudaOomError, terminal_status=CUDA_OOM, cuda_oom=true, evidence matched on exact probe identity, exact two-UUID binding, runtime/model pre+post verify, CPU/GPU cleanup, workspaces destroyed.
- Only after both root failure gates PASS, merge green activation PR #193 (head a2a002c8b23829c5220f9e64099f9d7a94bfe7b7), install the exact resulting merge SHA, and verify model-eval-dual-gpu alone is live while generic gpu-heavy remains DENY/admission-disabled.
- Issue exactly one `/lambda-ci-qwen35-dual-pilot 98f49e957073756411065a315514451fefd08ee6` comment on research-engine PR #123 and follow only that dedicated run.
- Accept the tensor-parallel pilot only if exact two-UUID binding holds, tensor_parallel_size=2, both UUIDs show >1 GiB peak model memory, exactly one synthetic image+text inference completes, and no scientific input/state, public acquisition, production-routing change, or persistent model server occurs.
- Read the final root-owned dual pilot provisioner receipt and require terminal success, exact workflow/candidate/model/runtime/two-UUID identity, runtime/model postverify, zero project CPU/GPU residue/quarantine, and destroyed job/staging workspaces.
- If all gates pass, mark bounded model-eval-dual-gpu authority VALIDATED. Keep generic gpu-heavy DENY unless a separate generic heavy-workload policy is explicitly designed and accepted.

## Blockers / gates

- Expanded Qwen runtime drift blocks the dual timeout/OOM gates: the canonical runtime currently has 54451 files / 6241 directories / 4 symlinks instead of the accepted 53583 / 6069 / 4, and exact accepted-tree restoration has not yet been proven. Read tasks/active/workspace-lambda-execution-policy-v1.runtime-drift-recovery.md before any further host action.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
