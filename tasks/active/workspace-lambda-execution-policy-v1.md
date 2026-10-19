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

Both root-authored dual failure gates are VALIDATED PASS. Reconcile the six-file activation diff from stale PR #193 head a2a002c8b23829c5220f9e64099f9d7a94bfe7b7 onto current main without changing its bounded semantics: live-enable only model-eval-dual-gpu, set that workload to EXISTING_P5_CAPABILITY/admission_enabled_after_enforcement=true, preserve exact model_eval_dual_gpu_v1/two-UUID/workflow/model/runtime binding, and keep generic gpu-heavy DENY/admission disabled. Validate the restaged activation against current main, merge only after green CI, then install the exact resulting merge SHA on Lambda and verify the activated installed manifest/policy identities plus healthy control plane before triggering research-engine PR #123.

## Remaining work

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
