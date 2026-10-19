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
- Remote checkpoint: 0f8375a889863c673fb79f76d83c7b94977a9252
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: e5a9b4c361ac790562fac5cf2f35f5a54f2bf58d
- Remote verified: true

## Next safe action

Do NOT rerun the dual-Qwen pilot. Workflow run 39188851843 is PASS and its model canary criteria are satisfied. Read only the final root-owned provisioner receipt /srv/workspace-ci/research-engine/logs/p5-b9e5d518-22e4-541b-9882-1969103be357-receipt.json and current host state. Require decision=RUNNER_EXITED_CLEANLY, terminal_status=SUCCEEDED, runner_exit_code=0, exact candidate/workload/profile/resource/workflow identity, exact two UUID/device binding, expanded_runtime_preverified/postverified=true with accepted b0cbb4ef... tree, promoted_model_preverified/postverified=true with exact Qwen object, project UID CPU/GPU cleanup true with no leaked GPU processes, runner/staging workspaces destroyed, no gpu-heavy lane quarantine, all three control-plane services active NRestarts=0, and no project CPU/GPU residue. If any final root condition fails, stop without rerunning the pilot.

## Remaining work

- Read the final root-owned dual pilot provisioner receipt and require terminal success, exact workflow/candidate/model/runtime/two-UUID identity, runtime/model postverify, zero project CPU/GPU residue/quarantine, and destroyed job/staging workspaces.
- If all gates pass, mark bounded model-eval-dual-gpu authority VALIDATED. Keep generic gpu-heavy DENY unless a separate generic heavy-workload policy is explicitly designed and accepted.

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
