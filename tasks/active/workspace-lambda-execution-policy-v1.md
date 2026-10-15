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
- Remote checkpoint: 360b7dfadcab15b5941b7b82057c3c6ab437beb8
- Remote verified: true

## Next safe action

Validate and merge the bounded model-eval-single-gpu policy/runtime implementation on workspace-control branch qwen35-model-eval-pilot. The dedicated research-engine default-branch pilot workflow is already merged at 360b7dfadcab15b5941b7b82057c3c6ab437beb8 with workflow blob 33373b6c9f73adf17b65adf37ceed82df5ade6bb after normal CI PASS. The workspace-control change must prove exact promoted-model admission freshness, exact single-A4500 resource binding, ordinary gpu-small model-forbidden separation, root verification of promoted model object 6e28e2560c07e7dabab92c55dbfb6941d5a7a75c8068bdc7a98115d8dc62072c via trusted-cache manager blob a97cb0be0e8f1f53504b33aed7c31a5aa6cb7807, and exact expanded runtime binding. After static validation/merge, install only the exact merged workspace-control SHA on Lambda, verify all bound identities, create one harmless open research-engine pilot candidate PR, invoke /lambda-ci-qwen35-pilot <exact PR head>, and accept only one synthetic non-scientific image+text inference with complete cleanup/evidence. gpu-heavy and dual-GPU remain denied.

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
