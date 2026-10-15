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
- Remote checkpoint: effc5b2f39fe897f4b9dc9fe6767d2002ee81cdb
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: fa0ff6f1a4a46fd0295e45df401aa8361d220c86
- Remote verified: true

## Next safe action

Audit the already-promoted Qwen3.5-4B model object 6e28e2560c07e7dabab92c55dbfb6941d5a7a75c8068bdc7a98115d8dc62072c, promoted runtime object 23a47f27bdb6bec63955b901080fc0926cffee8cf081d010195613789bc5bbf4, expanded runtime receipt/tree digest b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63, and current gpu-small admission/workflow policy to determine the minimum bounded offline model-eval pilot. Do not enable gpu-heavy or dual-GPU. Keep exact Qwen revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a, exact single accepted GPU UUID GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea, no public model acquisition, no production/scientific-state mutation, no persistent model server, and complete post-run cleanup/evidence. If a model-eval workload class remains non-live, implement and validate only the minimal root-owned policy/workflow expansion needed for this single offline pilot before any model load.

## Remaining work

- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small under the already-promoted model/runtime identities.
- Decide separately whether gpu-heavy or dual-GPU should ever be accepted; they remain denied.

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
