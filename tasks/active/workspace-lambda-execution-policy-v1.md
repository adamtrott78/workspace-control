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

Install exact workspace-control merge 6752ed4cb3018e1482467cef4a67ea5e89707792 on Lambda using the accepted bootstrap script blob 1f1203a17567ff95302938afd9d8060723407d31 with WORKSPACE_CI_P5_INSTALL_AUTHORIZED=YES, WORKSPACE_CI_P5_EXPECTED_SHA=6752ed4cb3018e1482467cef4a67ea5e89707792, and WORKSPACE_CI_P5_ACTIVATE_CONTROLLER=YES from a clean exact-SHA checkout/worktree. After install, require installed manifest blob 3bc3f37d0ae52c376228efc7792020d763b1eb9c, workload-policy blob 7efec0a8b951176d1f7b93e88b97a53f00b2091f, unchanged admission/provisioner/service/runtime/probe/cache-manager/profile/pins identities, model-eval-dual-gpu present in live_enabled_workload_classes with EXISTING_P5_CAPABILITY/admission true, generic gpu-heavy DENY/admission false, accepted runtime still b0cbb4ef..., all three services active NRestarts=0, and zero project CPU/GPU residue. Do not trigger research-engine PR #123 until this exact installed activation identity is verified.

## Remaining work

- Install exact workspace-control activation merge 6752ed4cb3018e1482467cef4a67ea5e89707792 on Lambda, then verify installed manifest blob 3bc3f37d0ae52c376228efc7792020d763b1eb9c and policy blob 7efec0a8b951176d1f7b93e88b97a53f00b2091f, exact unchanged executable/runtime/probe identities, model-eval-dual-gpu live, generic gpu-heavy DENY, and all three services healthy with NRestarts=0.
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
