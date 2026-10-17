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

Resume the already-installed exact workspace-control SHA 33470cceb6b3b3f63b2b0e8adfee940dc89b1329 no-model loopback/Gloo canary only; do not reinstall and do not rerun accepted post-install identity checks. The corrected canary workdir/probe setup passed, and Python executed inside the exact model network sandbox. The first network assertion then failed only because the harness required denied connect_ex() to return EPERM/EACCES/EAFNOSUPPORT; actual 127.0.0.2 connect_ex returned EAGAIN=11. systemd IPAddressAllow/Deny semantics make allow entries take precedence over deny entries, but do not define a specific userspace errno for cgroup-BPF filtered connections. Replace the errno classifier with a deterministic known-live denied-endpoint proof: bind/listen on 127.0.0.2 inside the probe, then require a client connect to that live listener to return nonzero while 127.0.0.1 live listener/client succeeds. Retain static proof that private-network IPAddressDeny rules are present rather than inferring policy from connecting to an arbitrary inactive private endpoint. Then prove exact expanded-runtime torch.distributed Gloo world_size=1 init/barrier/destroy with GLOO_SOCKET_IFNAME=lo and NCCL_SOCKET_IFNAME=lo, followed by model/runtime/control-plane/zero-residue verification. Only after PASS issue one next /lambda-ci-qwen35-pilot comment on unchanged PR #118 head dd8d15bdb61509f76e92a47cab2d937a8d45069b.

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
