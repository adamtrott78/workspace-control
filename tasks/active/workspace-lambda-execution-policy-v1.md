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
- Remote checkpoint: 4716726d7b705158f12005ee23daecb51b66e259
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 9b025b3b1092d1c4e0c1f98678472341d26ee354
- Remote verified: true

## Next safe action

Install and activate exact workspace-control 4716726d7b705158f12005ee23daecb51b66e259 on Lambda from a fresh detached clean worktree using the accepted P5 bootstrap with WORKSPACE_CI_P5_INSTALL_AUTHORIZED=YES, WORKSPACE_CI_P5_EXPECTED_SHA=4716726d7b705158f12005ee23daecb51b66e259, and WORKSPACE_CI_P5_ACTIVATE_CONTROLLER=YES. Do not restage the controller token and do not cancel active CPU run 37546267761 before activation. After activation, capture CPU/GPU NRestarts and active/running state, wait 8 seconds, and require zero restart delta. Then observe the existing CPU run 37546267761: the corrected controller must either recover ACCEPTED/terminal durable provision state without a second JIT/root grant, or remove only an orphaned exact-name/same-scale-set runner registration when root state is MISSING and regenerate JIT once. Require the run to reach actionable terminal evidence plus root receipt/cleanup before gpu-small acceptance. Use /lambda-ci-cancel <run_id> only if a new P5 failure makes cancellation necessary. Do not enable model-scale classes or gpu-heavy.

## Remaining work

- Install and activate exact deterministic-JIT-recovery workspace-control 4716726d7b705158f12005ee23daecb51b66e259, allow active CPU run 37546267761 to recover through durable provision-state reconciliation, then validate terminal CPU receipt/cleanup before launching gpu-small acceptance.
- Implement trusted acquisition/quarantine/promotion and read-only content-addressed model/runtime cache semantics.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Lambda still runs 4d4d14480f2cd6b573e33b10efc61a81a316327a and the CPU controller is crash-looping on deterministic JIT runner 409 for active run 37546267761. Install exact 4716726d7b705158f12005ee23daecb51b66e259 before further acceptance evaluation.
- After exact 4716726d activation, prove CPU/GPU controllers remain active/running with zero restart delta while the existing run 37546267761 is allowed to recover; do not trigger another CPU run until this active run reaches actionable terminal evidence or is explicitly canceled for a P5 reason.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
