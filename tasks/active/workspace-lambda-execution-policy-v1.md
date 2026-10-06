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
- Remote checkpoint: d2326042f49ae1bd771c33b1ce56f49795827661
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 12dd0f2f9510f682f0b62fe8fdc9a63494da8d6d
- Remote verified: true

## Next safe action

On the Lambda host from the normal operator account, use the clean workspace-control checkout and fast-forward it to exact canonical main d2326042f49ae1bd771c33b1ce56f49795827661. Verify the checkout is clean and HEAD is exact, then run the canonical scripts/bootstrap_lambda_ci_p5.sh via sudo with WORKSPACE_CI_P5_INSTALL_AUTHORIZED=YES and WORKSPACE_CI_P5_EXPECTED_SHA=d2326042f49ae1bd771c33b1ce56f49795827661. Preserve the generated install receipt under ~/adamArchives/Adam/workspace-control-tmp/. After live install PASS, create/choose a non-scientific research-engine candidate PR and trigger the existing trusted /lambda-ci-p5 <exact_sha> and /lambda-ci-p5-gpu <exact_sha> workflows. Require both GitHub jobs and root receipts to prove v2 admission identity, exact trusted workflow blob/candidate binding, unchanged cpu-test/gpu-small isolation, and residue-free cleanup before marking admission_manifest_and_enforcement VALIDATED. Do not enable any model-scale class or gpu-heavy in this stage.

## Remaining work

- Install canonical workspace-control d2326042f49ae1bd771c33b1ce56f49795827661 on Lambda through the exact-SHA root bootstrap and live-validate admission-v2 CPU and gpu-small receipts.
- Implement trusted acquisition/quarantine/promotion and read-only content-addressed model/runtime cache semantics.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Live admission-v2 activation requires reviewed sudo execution of the exact-SHA workspace-control bootstrap on Lambda. The accepted self-hosted runner and credential-blind provisioner intentionally cannot install or upgrade root services.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
