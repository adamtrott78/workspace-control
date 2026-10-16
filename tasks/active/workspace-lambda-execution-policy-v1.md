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
- Remote checkpoint: 89191de6821ed29c4f8494834e7c006e4725d8f9
- Remote verified: true

## Next safe action

Validate and merge workspace-control branch qwen35-pilot-workflow-repin. It must repin the model-eval-single-gpu trusted workflow to corrected research-engine main 89191de6821ed29c4f8494834e7c006e4725d8f9 / workflow blob fe83ad7d5e5e08335f4ad6e1acccceceaf4cafd5, project-manifest blob fe81231bf600cd37fc74dcbfc6ff72f20bfe965b, and workload-policy blob b5c0c502003b071e47e3da7724b6cb4b72538fe0, without changing model/runtime/GPU authority. After FULL_INTEGRATION PASS and merge, reinstall only that exact merged workspace-control SHA on Lambda with the accepted P5 bootstrap, verify the corrected manifest/policy identities plus existing trusted-cache/model/runtime/control-plane identities and zero residue, then confirm PR #118 remains open at exact head dd8d15bdb61509f76e92a47cab2d937a8d45069b. Only then issue exactly one second /lambda-ci-qwen35-pilot dd8d15bdb61509f76e92a47cab2d937a8d45069b comment and accept the pilot only if one synthetic image+text inference completes with exact pre/post identities and complete cleanup. Do not enable gpu-heavy before the single-GPU pilot is VALIDATED; gpu-heavy audit/design may proceed in parallel but activation remains gated.

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
