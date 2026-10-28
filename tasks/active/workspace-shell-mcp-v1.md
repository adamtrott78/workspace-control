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

Give ChatGPT durable, auditable, least-privilege command-execution access to the Lambda workspace through a separate private MCP/plugin so workspace-control tasks can execute and inspect bounded shell operations directly without using the operator as a copy/paste terminal relay, while preserving explicit provenance, credential isolation, rollback boundaries, and separately auditable privileged authority.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-mcp-v1-implementation
- Remote checkpoint: 4a3b6735b53a7934fb0a7bb52cbbf320915bd8ca
- Remote verified: true

## Next safe action

Continue implementing and adversarially testing Workspace Shell v1 on PR #552. Do not stop for independent-review handoffs. Preserve exact-SHA/CI boundaries and do not perform live Lambda installation, tunnel/key provisioning, OS-principal creation, privileged-helper installation, systemd activation, Heartbeat mutation, or project-controller mutation until the host-specific installation plan is validated and explicitly activated by the operator.

## Remaining work

- Continue pre-installation hardening of Workspace Shell v1 without external reviewer handoffs.
- Fix receipt-reader ownership/access semantics so root-written audit receipts are readable by the frontend without granting write authority.
- Permit safe git-read inspection of a dirty checkout while keeping executable profiles fail-closed on dirty source.
- Expand adversarial tests for receipt ownership/group access, dirty-source behavior, cancellation, cgroup cleanup and secret-minimized argv receipts.
- Create host-attestation and installation artifacts for exact UIDs/GIDs, directories, sockets, systemd units, tunnel mTLS material, rollback and emergency disable.
- Run exact-head Workspace Control Validation after each implementation checkpoint.
- After repository validation, obtain fresh read-only Lambda host attestation and then proceed to installation only with explicit operator activation authority.

## Blockers / gates

- Fresh live Lambda host attestation is required before host-specific unit/UID/GID/socket/mount assumptions are accepted.
- Repository implementation and installation artifacts must pass exact-head CI and adversarial validation before live installation.
- Tunnel/key provisioning, root/job-launcher/broker installation, systemd activation and live Lambda execution remain prohibited until the host-specific installation plan is validated and the operator authorizes activation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
