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
- Remote checkpoint: 83ead40b347f55937235f14bc71a73397741cfcb
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: dcb351a33710ad9cc6697987b0d5b2dd92513dd3
- Remote verified: true

## Next safe action

Install the validated workspace-control adversarial-runtime integration on Lambda from the exact current main produced by the task-only checkpoint following implementation merge 83ead40b347f55937235f14bc71a73397741cfcb. Use bootstrap_lambda_ci_p5.sh with exact-SHA guard and controllers active; first verify the existing expanded runtime path, durable receipt, and trusted-cache manager blob are present and unchanged. Then trigger exactly one naturally required gpu-small run through the trusted research-engine workflow at main dcb351a33710ad9cc6697987b0d5b2dd92513dd3 / workflow blob 427498aad2ab3fa57fd8035461b5817282e5d96b against an exact PR head SHA. Treat that run as the first live adversarial acceptance: require runtime mutation denial, exact runtime identity, bounded CUDA, post-run tree re-verification, zero project/GPU process residue, job/staging cleanup, and durable root receipt. Do not load model weights or perform inference. Do not create any extra run solely for measurement.

## Remaining work

- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

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
