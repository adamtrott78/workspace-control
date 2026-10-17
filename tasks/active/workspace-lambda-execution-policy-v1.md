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
- Remote checkpoint: bdb2addadbe8a90eb917dee1b026ad4576933b1f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: b345091924bf175777ac52c5549b10c387cbdf14
- Remote verified: true

## Next safe action

Confirm research-engine candidate PR #118 remains open at exact head dd8d15bdb61509f76e92a47cab2d937a8d45069b, then issue exactly one /lambda-ci-qwen35-pilot dd8d15bdb61509f76e92a47cab2d937a8d45069b comment. Follow that exact dedicated workflow run through runner allocation, exact PR/model/runtime binding, model initialization, one synthetic image+text inference, uploaded pilot receipt, root execution receipt, runtime pre/post model+runtime verification, terminal status, and cleanup. Accept only if model_weights_loaded=true, model_inference_performed=true, inference_calls=1, scientific_input_used=false, scientific_state_materialized=false, production_routing_changed=false, public_model_acquisition=false, no persistent model server, exact accepted GPU UUID, and complete project/GPU cleanup. If it fails, do not trigger another retry until uploaded receipt/root evidence is diagnosed. gpu-heavy activation remains gated until the single-GPU pilot is VALIDATED.

## Remaining work

- Run and accept the first offline Qwen3.5-4B pinned-model pilot on gpu-small using one synthetic non-scientific image+text inference.
- After the pilot is accepted, decide separately whether gpu-heavy or dual-GPU should ever be accepted; they remain denied.

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
