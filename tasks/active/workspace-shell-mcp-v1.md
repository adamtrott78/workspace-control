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
- Remote branch: workspace-shell-mcp-v1-current-main
- Remote checkpoint: f537af52b622c1f8a8265186778d5897fc86c1fd
- Remote verified: false

## Next safe action

Run the exact-head self-hosted Workspace Control validation route on PR #573 with the explicit `host-attest` suffix. The repository test will execute secret-averse read-only plugins/workspace-shell/install/host_attest.py against the exact checked-out PR head on the Lambda GitRunner and emit one bounded WORKSPACE_SHELL_HOST_ATTESTATION_JSON record. Do not install or activate Workspace Shell yet. After the attestation is captured, validate it, bind it durably, render the exact host-specific installation bundle, and re-run exact-head CI.

## Remaining work

- Capture fresh exact-head read-only Lambda host attestation through PR #573 self-hosted GitRunner route `/workspace-control-validate <HEAD> host-attest`.
- Validate and durably bind the secret-averse attestation to the exact Workspace Shell source head.
- Render and validate the exact host-specific installation bundle, including explicit distinct UIDs/GIDs, runtime/source paths, systemd units, tunnel-client staging, rollback and emergency disable.
- Keep privileged helper registry and operator trust/revocation stores empty/fail-closed for initial unprivileged commissioning.
- Run exact-head hosted and self-hosted validation on the rendered commissioning candidate.
- With explicit operator activation authority, perform one bounded manual installation/activation transaction, verify hostile-worker denials and end-to-end bounded command execution, then connect the dedicated ChatGPT plugin/tunnel.

## Blockers / gates

- Fresh exact-head Lambda host attestation has not yet been captured on PR #573.
- Live Workspace Shell installation/activation remains explicitly unauthorized until the attestation-derived bundle passes exact-head validation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
