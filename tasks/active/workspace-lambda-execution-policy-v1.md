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
- Remote checkpoint: d5e6fe24b7def6211aba4f7f1729a8de75fd1781
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 8a74d1f0061a687b7a7e30bbd9f846919424b79e
- Remote verified: true

## Next safe action

Validate and merge workspace-control branch qwen35-cache-manager-mode-fix. The fix must change only the trusted-cache manager deployed mode from root:root 0755 to root:root 0555 and preserve exact cache-manager content blob a97cb0be0e8f1f53504b33aed7c31a5aa6cb7807; unit/full-integration validation must pass. Then reinstall the exact merged workspace-control SHA on Lambda with the existing authorized P5 bootstrap and rerun the installation/identity gate from the promoted-model verification step forward. Require the installed cache-manager stat to be root:root regular file mode 555 before calling verify_promoted_model_binding. Do not trigger /lambda-ci-qwen35-pilot, load Qwen weights, or perform inference until the corrected host identity gate passes. gpu-heavy and dual-GPU remain denied.

## Remaining work

- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small under the already-promoted model/runtime identities.
- Decide separately whether gpu-heavy or dual-GPU should ever be accepted; they remain denied.

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
