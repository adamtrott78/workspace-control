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
- Remote checkpoint: 038e6224cbd1d7e5f2dce21708509c5f1c8f826d
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: dcb351a33710ad9cc6697987b0d5b2dd92513dd3
- Remote verified: true

## Next safe action

Install workspace-control exact SHA 038e6224cbd1d7e5f2dce21708509c5f1c8f826d on Lambda using the accepted exact-SHA bootstrap path. This changes only the expanded-runtime tree-digest implementation/tests; trusted runtime object/receipt/tree digest, policy epoch, trusted workflow blob, trusted-cache manager, model authority, and gpu-heavy denial remain unchanged. Verify installed lambda_ci_runtime.py blob matches this SHA and that the root provisioner/controller services return active with zero unexpected restarts. Then cancel or otherwise terminalize the already-failed queued GitHub workflow run 37732928088 without re-executing it, and trigger one fresh adversarial gpu-small run from a new exact candidate PR head/comment so admission gets a new request/job identity. Require pre-execution verifier to match b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63 before candidate start. Do not load model weights or perform inference.

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
