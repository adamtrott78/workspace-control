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
- Remote checkpoint: 01a95b61410e2f427b9885a19e6a0b9c5ee60a38
- Remote verified: true

## Next safe action

LIVE ACTIVATION IS COMPLETE. Do not reinstall or rerun commissioning. Exact accepted Workspace Shell operator/runtime head is 01a95b61410e2f427b9885a19e6a0b9c5ee60a38; Validation #1463/run 41273806752 succeeded; activation blob 815caf6bc0462ab6b77f414b90dc9ddb0b8a458d; source snapshot remains f999b25a866f25c95243cbbd6d1377a799fafb78. Lambda passed LOCAL_MTLS_HEALTH, real LOCAL_MCP_INITIALIZE, TUNNEL_READY, and SERVICES_ACTIVE_BOOT_DISABLED, and wrote /var/lib/workspace-shell/commissioning/activation-receipt.json. NEXT: connect the dedicated tunnel as a private ChatGPT Workspace Shell plugin/connector and perform live acceptance: tool discovery, runtime/Git inspection, one bounded unprivileged execution, denial tests, and receipt verification. Do not enable units at boot and do not add privileged helpers until that acceptance passes.

## Remaining work

- Connect the dedicated Workspace Shell tunnel as a private ChatGPT plugin/connector in the target ChatGPT workspace.
- Verify tool discovery and perform a live workspace_shell_inspect/runtime inventory call.
- Verify exact Git inspection of workspace-control and one bounded unprivileged execution through Workspace Shell.
- Run denial tests for unauthorized filesystem paths, credential/secret reads, arbitrary-shell escape shapes, and privileged helper invocation; all must fail closed.
- Inspect the resulting Workspace Shell execution/audit receipts and the commissioning activation receipt.
- Only after live acceptance decide whether the four Workspace Shell services should become boot-enabled.
- After Workspace Shell acceptance, return to workspace-github-actions-control-plane-protocol-redesign-v1 and use Workspace Shell as the terminal transport for the remaining v3 migration, adding only narrowly reviewed privileged helpers when a concrete migration operation requires them.

## Blockers / gates

- No commissioning blocker remains: Workspace Shell is live on Lambda and the dedicated Secure MCP Tunnel reached readiness.
- ChatGPT-side plugin/connector live acceptance has not yet been completed; until it passes, do not treat Workspace Shell as the authoritative terminal transport for other durable tasks.
- All Workspace Shell systemd units remain boot-disabled intentionally pending live acceptance.
- Privileged helper registry and operator trust stores remain empty/fail-closed; no privileged helper execution is currently authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
