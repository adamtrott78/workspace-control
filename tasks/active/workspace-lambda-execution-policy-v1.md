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
- Remote checkpoint: d43ad9a27ad5c4769f63519787612c3f549be13d
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 8a74d1f0061a687b7a7e30bbd9f846919424b79e
- Remote verified: true

## Next safe action

Create one harmless open research-engine pilot candidate PR whose change is explicitly non-scientific and has no production/scientific-state effect. Record its exact PR head SHA. Then, from that PR, issue exactly one /lambda-ci-qwen35-pilot <exact-head-sha> comment so the trusted default-branch workflow submits one model-eval-single-gpu request through the accepted GPU controller. Accept only the exact promoted Qwen3.5-4B object 6e28e2560c07e7dabab92c55dbfb6941d5a7a75c8068bdc7a98115d8dc62072c at revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a on exact expanded runtime tree b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63 and accepted GPU UUID GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea. The pilot may perform exactly one bounded synthetic image+text inference, with no scientific input, no production routing change, no public model acquisition, no persistent model server, and complete post-run project/GPU cleanup. After the run, inspect the GitHub job, uploaded pilot receipt, provisioner/root execution receipt, runtime pre/post model+runtime verification, terminal status, and residue. Mark qwen35_model_eval_pilot VALIDATED only if all acceptance evidence is PASS; otherwise fail closed and diagnose without retrying blindly.

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
