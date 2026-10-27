<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-mcp-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-mcp-v1
- Title: Workspace Shell MCP v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Give ChatGPT durable, auditable, least-privilege command-execution access to the Lambda workspace through a separate private MCP/plugin so workspace-control tasks can execute and inspect bounded shell operations directly without using the operator as a copy/paste terminal relay, while preserving explicit provenance, credential isolation, rollback boundaries, and independently reviewable privileged authority.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-mcp-v1-implementation
- Remote checkpoint: be67b71ff60da30d80ddec26453e0f1e92a10780
- Remote verified: true

## Next safe action

Implement and adversarially test Workspace Shell v1 in repository only on branch workspace-shell-mcp-v1-implementation, preserving the accepted authority contract. No Lambda installation, tunnel/key provisioning, root authority activation, Heartbeat mutation, or project-controller mutation.

## Remaining work

- Implement the MCP policy frontend, fixed profile grammar, task/provenance validation, bounded receipt handling and local Unix-socket clients.
- Implement repository-only root-owned job-launcher and reviewed-helper broker protocols with peer-credential checks, hostile-worker isolation plan enforcement, approval verification and fail-closed replay/revocation logic.
- Add adversarial tests covering argv/path/profile confusion, worker/control-plane separation, approval forgery/replay/expiry/revocation/binding failures, output limits and receipt integrity.
- Run Workspace Control Validation and plugin-specific tests; fix all failures.
- Request fresh independent exact-head implementation review. Do not install anything on Lambda.
- After implementation acceptance, obtain fresh read-only host attestation and design the exact installation units/UIDs/sockets/mounts/rollback before a separate installation review.

## Blockers / gates

- Fresh live Lambda host attestation is required before installation-specific unit/UID/socket/mount choices are accepted.
- Repository implementation must pass adversarial tests and independent exact-head implementation review before installation.
- Tunnel/key provisioning, root/job-launcher/broker installation, systemd activation and live Lambda execution remain prohibited.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
