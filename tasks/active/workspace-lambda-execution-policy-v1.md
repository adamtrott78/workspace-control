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

Validate and merge research-engine branch qwen35-pilot-cold-start-budget-fix. The only functional change must be the workflow-local model initialization ceiling from 120s to 240s; preserve the 60s synthetic inference ceiling, max_tokens=32, exactly one inference call, exact promoted-model/runtime/GPU binding, and all sandbox/security controls. After normal research-engine CI PASS/merge, repin the exact new research-engine main/workflow blob into workspace-control project manifest/workload policy/tests, run canonical workspace-control validation, merge, and install only the exact merged identity repin on Lambda. Reverify the trusted workflow pin plus unchanged runtime c7e0521d3270c2d1171ad3c4786bcf3de39781c4, promoted Qwen object, expanded runtime, control plane, and zero residue. Confirm PR #118 is still open at exact head dd8d15bdb61509f76e92a47cab2d937a8d45069b, then issue exactly one next pilot trigger. Accept only if the one synthetic image+text inference completes and all post-run receipts/cleanup are PASS. gpu-heavy remains activation-gated until the single-GPU pilot is VALIDATED.

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
