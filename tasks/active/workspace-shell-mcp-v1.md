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
- Remote checkpoint: d3b85d9c86edbea40d6a42e8d4c29ed6c1c98350
- Remote verified: true

## Next safe action

Run one final secret-averse read-only Lambda host attestation against the exact current PR #573 head after task-state synchronization. The final probe must prove fixed uid/gid 41010/41011/41012 are unused, planned Workspace Shell names/paths/units remain absent, port 8797 remains free, bubblewrap/user namespaces still pass, and the exact source checkout is clean. Do not install or activate Workspace Shell yet. After final attestation passes, bind the evidence durably, render/validate the unsealed host-specific bundle, and prepare the separately authorized activation transaction.

## Remaining work

- Capture final exact-head read-only Lambda host attestation proving fixed numeric identities 41010/41011/41012 and all other pre-apply collision/isolation gates.
- Durably bind the final secret-averse attestation and its digest to the verified Workspace Shell commissioning source.
- Render and validate the unsealed host-specific install bundle from the final attestation; helper registry and operator trust/revocation stores remain empty/fail-closed.
- Prepare an explicit bounded activation operator that installs fixed principals/paths/runtime, creates dedicated signing/TLS/tunnel material during the activation transaction, seals the bundle from the public tunnel client certificate, installs units disabled-by-default, and has exact rollback/emergency-disable semantics.
- With explicit operator activation authority, execute the commissioning transaction, verify hostile-worker denials and local bounded command execution, then connect the dedicated ChatGPT plugin/tunnel.
- After live end-to-end acceptance, close the Workspace Shell task and return to the GitRunner v3 fleet migration using Workspace Shell as the terminal transport.

## Blockers / gates

- One final exact-head Lambda host attestation is required because the preliminary probe did not check the now-fixed numeric UID/GID assignments.
- Live Workspace Shell installation/activation remains explicitly unauthorized until the final attestation-derived unsealed bundle passes exact-head validation and a separate operator activation transaction is frozen.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
