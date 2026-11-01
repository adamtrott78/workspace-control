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
- Remote checkpoint: 483c3e8bdf8fc0e1db58ff836a1d136e49df4112
- Remote verified: true

## Next safe action

ACCOUNT-SIDE GATE: create a new dedicated Workspace Shell Secure MCP Tunnel in OpenAI Platform and associate it with the target ChatGPT workspace. Create a separate restricted runtime API key with Tunnels Read + Use only; do not paste the key into chat. Then execute the exact validated plugins/workspace-shell/install/activate_live.sh from the frozen PR #573 head. The operator requires the tunnel ID, performs a no-mutation preflight, asks for literal ACTIVATE_WORKSPACE_SHELL before mutation, prompts for the runtime key with hidden input, and rolls back automatically on any failure before terminal commit. After PASS, connect the tunnel as a private ChatGPT plugin and perform live acceptance before enabling any unit at boot.

## Remaining work

- In OpenAI Platform tunnel settings, create a dedicated Workspace Shell tunnel (do not reuse Heartbeat) and associate it with the ChatGPT workspace.
- Create a dedicated restricted runtime API key with only Tunnels Read + Use; keep the secret value off chat/GitHub.
- Freeze one exact PR #573 operator head after final task/handoff synchronization and successful Workspace Control Validation; verify the activate_live.sh blob before execution.
- Run the activation operator from that exact head. It must pass preflight before asking for ACTIVATE_WORKSPACE_SHELL, then prompt for the runtime key with hidden input, and end with local mTLS/tunnel readiness while all services remain disabled at boot.
- Connect the dedicated tunnel as a private ChatGPT Workspace Shell plugin and perform live tool acceptance: runtime/unit inspection, exact Git inspection, one bounded unprivileged execution, denial tests, receipt verification, and empty privileged-helper denial.
- After v1 live acceptance, decide boot enablement and then add only narrowly reviewed privileged helpers actually needed for the remaining GitRunner v3 migration.
- Return to the GitRunner v3 fleet migration using Workspace Shell as the terminal transport.

## Blockers / gates

- A dedicated Workspace Shell Secure MCP Tunnel has not yet been provisioned/associated with the target ChatGPT workspace.
- A dedicated runtime API key with Tunnels Read + Use has not yet been provisioned on the operator side; its secret must never be pasted into chat or committed.
- Live activation and ChatGPT plugin acceptance have not yet been executed. The four Workspace Shell services must remain absent until the explicit activation transaction.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
