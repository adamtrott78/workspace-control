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

Install exact workspace-control SHA bdb2addadbe8a90eb917dee1b026ad4576933b1f on Lambda using the accepted P5 bootstrap. Verify installed runtime blob c7e0521d3270c2d1171ad3c4786bcf3de39781c4 and unchanged bootstrap/admission/provisioner/service/trusted-cache/manifest/policy identities. Before any model run, execute one no-model canary under the exact model-eval network sandbox including RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK, existing loopback/private IP policy, GLOO_SOCKET_IFNAME=lo, and NCCL_SOCKET_IFNAME=lo. Directly prove Linux interface enumeration for lo succeeds, 127.0.0.1 TCP succeeds, a known-live 127.0.0.2 endpoint remains blocked, and exact expanded-runtime torch.distributed Gloo world_size=1 init/barrier/destroy succeeds. Then reverify promoted Qwen object/expanded runtime/control-plane/zero residue/quarantine. Confirm candidate PR #118 remains open at exact head dd8d15bdb61509f76e92a47cab2d937a8d45069b. Only after PASS issue exactly one next /lambda-ci-qwen35-pilot comment. gpu-heavy remains activation-gated until the single-GPU pilot is VALIDATED.

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
