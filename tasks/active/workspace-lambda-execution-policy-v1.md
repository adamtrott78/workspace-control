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

Resume the already-installed exact workspace-control SHA 33470cceb6b3b3f63b2b0e8adfee940dc89b1329 loopback/Gloo host gate from the no-model canary only; do not reinstall. Service-runtime identity already PASS. The first canary attempt returned systemd exit status 200 because the harness placed WorkingDirectory under /run/workspace-ci, whose canonical bootstrap permissions are root:workspace-ci-controller 0750 and intentionally not traversable by ci-research-engine. Recreate the canary under /srv/workspace-ci/research-engine/jobs using the same runtime ownership pattern as real jobs: per-canary directory mode 0700 owned ci-research-engine:ci-research-engine, immutable/read-only probe file, same model-eval network sandbox properties. Prove allowed 127.0.0.1 TCP, denied 127.0.0.2 and representative private address, and exact expanded-runtime torch.distributed Gloo world_size=1 initialization/destroy. Then reverify promoted Qwen object/expanded runtime/control-plane/zero residue/quarantine. Only after PASS issue one next /lambda-ci-qwen35-pilot comment on unchanged PR #118 head dd8d15bdb61509f76e92a47cab2d937a8d45069b.

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
