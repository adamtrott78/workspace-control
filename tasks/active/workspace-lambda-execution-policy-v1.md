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
- Remote checkpoint: 166b42763d20c465c7f136efc6a97191362431fb
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: b345091924bf175777ac52c5549b10c387cbdf14
- Remote verified: true

## Next safe action

Validate and merge workspace-control branch qwen35-loopback-distributed-fix. Because scripts/lambda_ci_runtime.py changes, require Python regression, pinned Go/controller validation, and FULL_INTEGRATION. The change must remain model-bound only: model-eval keeps ProtectProc=invisible + ProcSubset=all, gains only IPAddressAllow=127.0.0.1/32 and ::1/128 plus GLOO_SOCKET_IFNAME=lo and NCCL_SOCKET_IFNAME=lo, while all existing IPAddressDeny entries remain and ordinary gpu-small stays ProtectProc=invisible + ProcSubset=pid with no loopback exception/interface overrides. After merge, install the exact merged SHA on Lambda and before any model run perform a root synthetic loopback canary using the same model-eval network sandbox properties: prove an AF_INET TCP listener/client can communicate on 127.0.0.1, prove a Gloo single-process group can initialize on lo using the exact expanded runtime, and prove a representative denied private address remains blocked. Reverify exact model/runtime/control-plane/zero-residue identities. Only after that canary passes, issue exactly one next /lambda-ci-qwen35-pilot comment on unchanged PR #118 head dd8d15bdb61509f76e92a47cab2d937a8d45069b. gpu-heavy remains activation-gated until single-GPU pilot VALIDATED.

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
