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
- Remote checkpoint: 4a3b6735b53a7934fb0a7bb52cbbf320915bd8ca
- Remote verified: true

## Next safe action

Synchronize this implementation checkpoint into the derived handoff, validate the resulting exact PR #552 head, then record a fresh independent implementation review request. Do not merge PR #552 or mutate Lambda, provision tunnel/key material, create OS principals, install root/job-launcher/broker/helper authority, modify Heartbeat, or activate any project controller.

## Remaining work

- Validate the state-only implementation-review synchronization head.
- Request fresh independent exact-head implementation review for PR #552, binding the review to code/test checkpoint 4a3b6735b53a7934fb0a7bb52cbbf320915bd8ca and successful validation run #1054.
- Do not merge or install the implementation until independent review returns NO_BLOCKING_FINDING on the exact synchronized head.
- After implementation acceptance, obtain fresh read-only Lambda host attestation and design the exact installation units, UIDs/GIDs, sockets, mounts, cgroups, credentials, tunnel binding, rollback and emergency-disable procedure.
- Submit that installation plan and exact artifacts for a separate independent installation review before any live Lambda mutation or activation.

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
