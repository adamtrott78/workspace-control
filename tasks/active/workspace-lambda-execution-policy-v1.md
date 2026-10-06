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
- Remote checkpoint: 4bdfc2b4dc9a24e5536f227f679907a1fe9e74cf
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 12dd0f2f9510f682f0b62fe8fdc9a63494da8d6d
- Remote verified: true

## Next safe action

Cancel research-engine CPU run 37537640812 so the pre-f246 lifecycle attempt cannot consume a runner under the corrected controller. Lambda is already live on exact workspace-control f246800116aa1a390cdd1a31105bc74400e1c2f5 with CPU/GPU controllers and provisioner active/running and NRestarts=0 immediately after activation, so do not reinstall. After run 37537640812 is canceled, trigger a NEW trusted /lambda-ci-p5 f5ba8278d7dfa22e63623ddf51896a6dec002813 on research-engine PR #106; require CPU completion plus root receipt/cleanup before launching NEW /lambda-ci-p5-gpu f5ba8278d7dfa22e63623ddf51896a6dec002813. Do not count run 37537640812 as acceptance evidence and do not enable model-scale classes or gpu-heavy.

## Remaining work

- Cancel queued pre-f246 CPU run 37537640812, then run fresh non-scientific admission-v2 CPU and gpu-small acceptance against the live f246800116aa1a390cdd1a31105bc74400e1c2f5 controller and validate root receipts plus residue-free cleanup.
- Implement trusted acquisition/quarantine/promotion and read-only content-addressed model/runtime cache semantics.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Fresh pre-f246 CPU run 37537640812 is still queued and must be canceled before another acceptance trigger.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
