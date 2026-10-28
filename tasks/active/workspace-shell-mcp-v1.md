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
- Remote checkpoint: d827b5d18f9920412e1f68a22264a9abf0993886
- Remote verified: true

## Next safe action

Obtain fresh read-only Lambda host attestation for exact checkpoint d827b5d18f9920412e1f68a22264a9abf0993886 using the repository host_attest.py surface or an equivalently bounded existing Lambda execution surface. Do not request an independent reviewer. Do not install/activate Workspace Shell or provision secrets until the attestation-derived bundle is validated.

## Remaining work

- Obtain fresh read-only Lambda host attestation for exact checkpoint d827b5d18f9920412e1f68a22264a9abf0993886 without exposing secret contents.
- Render and validate the exact host-specific installation bundle from the attestation, including UIDs/GIDs, root-owned directories, sockets, mTLS material locations, frontend signing material locations, tunnel identity/profile, rollback and emergency disable.
- Keep privileged helper registry empty/fail-closed until an actual typed root mutation is needed; privileged helpers use operator-signed workspace-shell-approval.v2 rather than external reviewer records.
- Run exact-head Workspace Control Validation on every resulting implementation/state checkpoint.
- With explicit operator activation authority, install and start Workspace Shell in isolation, verify hostile-worker denials and end-to-end bounded command execution, then connect the dedicated ChatGPT plugin/tunnel.

## Blockers / gates

- Fresh read-only Lambda host attestation is required before exact host-specific UIDs/GIDs, runtime paths, tunnel-client path, bubblewrap/user-namespace behavior and systemd assumptions are accepted.
- Live installation still requires explicit operator activation authority after the host-specific bundle passes exact-head validation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
