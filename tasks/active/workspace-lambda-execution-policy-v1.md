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
- Remote checkpoint: ba3df4238902a382df9e807889ff048b98750012
- Remote verified: true

## Next safe action

Validate and merge workspace-control branch qwen35-cold-start-workflow-repin. This is an identity-only repin to research-engine main ba3df4238902a382df9e807889ff048b98750012 / trusted Qwen pilot workflow blob 31d77703d434b248aa50adf93568f9a13b89dc07, producing project-manifest blob 88694079e7c1c069533894f07c153f273601fd17 and workload-policy blob a21096e2b69e3c77c979d5e34b57d29fa1d77308. Executable workspace-control P5 code must remain unchanged from accepted bdb2addadbe8a90eb917dee1b026ad4576933b1f, including runtime blob c7e0521d3270c2d1171ad3c4786bcf3de39781c4. After canonical validation/merge, reinstall only the exact merged workspace-control SHA on Lambda, verify new manifest/policy/workflow identities plus unchanged bootstrap/admission/provisioner/service/runtime/trusted-cache/model/runtime/control-plane/zero-residue identities, and confirm PR #118 remains open at exact head dd8d15bdb61509f76e92a47cab2d937a8d45069b. Then issue exactly one next /lambda-ci-qwen35-pilot comment and accept only if one synthetic image+text inference completes with all post-run receipts/cleanup PASS. gpu-heavy remains activation-gated until single-GPU pilot VALIDATED.

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
