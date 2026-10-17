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

Perform the final root-owned acceptance read for request df8739fd-f7fa-5c34-8606-793099116668; do not rerun the model. Read /srv/workspace-ci/research-engine/logs/p5-df8739fd-f7fa-5c34-8606-793099116668-receipt.json and require phase=P5-provisioner-runtime, decision=RUNNER_EXITED_CLEANLY, terminal_status=SUCCEEDED, runner_exit_code=0, timed_out=false, wrapper_timeout_cleanup=true, automatic_retry_eligible=false, resource_exhausted=false, disk_pressure=false, cuda_oom=false, project_uid_process_cleanup=true, project_uid_gpu_process_cleanup=true, leaked_gpu_processes=[], runner_workspace_destroyed=true, staging_workspace_destroyed=true, expanded_runtime_preverified=true, expanded_runtime_postverified=true with no postverify error, promoted_model_preverified=true, promoted_model_postverified=true with no postverify error, jit_config_persisted=false, github_credential_present=false, persistent_project_home_writable=false, exact GPU target UUID GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea and cuda_visible_devices equal that UUID, and admission identity/candidate/workload binding matching the accepted run. Also require the job/staging directories absent, no ci-research-engine processes, no project GPU processes, no lane quarantine, and provisioner/CPU/GPU controllers active with NRestarts=0. If all PASS, mark qwen35_model_eval_pilot VALIDATED and move immediately to explicit gpu-heavy/dual-GPU implementation and acceptance; do not rerun the successful single-GPU model pilot.

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
