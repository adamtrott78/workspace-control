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
- Remote checkpoint: 33470cceb6b3b3f63b2b0e8adfee940dc89b1329
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: b345091924bf175777ac52c5549b10c387cbdf14
- Remote verified: true

## Next safe action

Resume the already-installed exact workspace-control SHA 33470cceb6b3b3f63b2b0e8adfee940dc89b1329 host gate from the first unfinished post-install assertion; do not reinstall. The install itself passed and all seven exact installed blobs matched through workload policy. The wrapper then exited before INSTALLED_IDENTITY=PASS because the final expanded-runtime executable check was evaluated as the interactive user rather than the ci-research-engine service account. Verify trusted-cache manager stat root:root 555 regular file and verify the exact expanded-runtime Python is executable as ci-research-engine (not as the interactive user), then run the no-model loopback/Gloo canary, model/runtime reverify, control-plane/residue checks, and only after PASS issue one next /lambda-ci-qwen35-pilot comment on unchanged candidate PR #118 head dd8d15bdb61509f76e92a47cab2d937a8d45069b. Do not reinstall or rerun accepted identity checks solely for reassurance.

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
