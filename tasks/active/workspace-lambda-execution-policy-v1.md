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
- Remote checkpoint: b1217e296ca939e344b619db474822f9ce611b82
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: ba3df4238902a382df9e807889ff048b98750012
- Remote verified: true

## Next safe action

Resume final root acceptance for successful single-GPU Qwen request df8739fd-f7fa-5c34-8606-793099116668 from the admission-identity assertion only; do not rerun the model, reinstall, or repeat already-passed root receipt checks. The prior acceptance harness reached line 86 after all earlier root receipt assertions passed and failed only because it incorrectly expected admission_identity.resource_class == 'gpu-small'. Canonical workload policy binds model-eval-single-gpu to resource_class 'model_eval_single_gpu_v1' while execution_profile remains 'gpu-small'. Validate remaining receipt admission identity with resource_class=model_eval_single_gpu_v1, then validate durable provisioner state/result, absent job/staging directories, no ci-research-engine CPU/GPU residue, no lane quarantine, and provisioner/CPU/GPU controllers active with NRestarts=0. If all PASS, mark qwen35_model_eval_pilot VALIDATED, close the inert candidate PR #118 if appropriate, and move immediately to explicit gpu-heavy/dual-GPU design and acceptance without rerunning the accepted single-GPU pilot.

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
