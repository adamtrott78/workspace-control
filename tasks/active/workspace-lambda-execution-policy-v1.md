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
- Remote checkpoint: 66856757d47788246a6fc5810542cffe522877cf
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 9b025b3b1092d1c4e0c1f98678472341d26ee354
- Remote verified: true

## Next safe action

Install and activate exact workspace-control 66856757d47788246a6fc5810542cffe522877cf on Lambda from a fresh detached clean worktree using the accepted P5 bootstrap with WORKSPACE_CI_P5_INSTALL_AUTHORIZED=YES, WORKSPACE_CI_P5_EXPECTED_SHA=66856757d47788246a6fc5810542cffe522877cf, and WORKSPACE_CI_P5_ACTIVATE_CONTROLLER=YES. Do not restage the controller token and do not cancel active CPU run 37546267761. After activation, require CPU/GPU controllers and provisioner active/running; capture CPU/GPU NRestarts, wait 8 seconds, and require zero restart delta. Inspect recent CPU/provisioner events for request fa97e66f-c71c-5e48-926a-129a7ecde8b3 / runner lambda-research-engine-8fb642f3900d: orphan cleanup may occur only when durable root state is MISSING, verified_at admission must no longer fail, and a provision request must either be accepted/recovered or produce a new explicit fail-closed error. Then inspect GitHub run 37546267761 for actionable terminal evidence; do not launch gpu-small until CPU receipt/cleanup are proven. Do not enable model-scale classes or gpu-heavy.

## Remaining work

- Install and activate exact workspace-control 66856757d47788246a6fc5810542cffe522877cf, preserve active CPU run 37546267761, prove restart-delta stability and successful verified_at admission/JIT recovery, then validate terminal CPU receipt/cleanup before launching gpu-small acceptance.
- Implement trusted acquisition/quarantine/promotion and read-only content-addressed model/runtime cache semantics.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Exact verified_at-compatible workspace-control 66856757d47788246a6fc5810542cffe522877cf is validated but not installed on Lambda. CPU controller remains stopped; install/activate exact 66856757 before evaluating the preserved queued CPU run again.
- After exact 66856757 activation, require CPU/GPU active/running with zero restart delta and allow existing run 37546267761 to recover through JIT-orphan reconciliation plus root admission; do not trigger another CPU run until this one reaches actionable terminal evidence or a new P5 failure requires cancellation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
