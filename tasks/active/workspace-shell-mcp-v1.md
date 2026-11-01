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

POST-REPAIR LIVE ACCEPTANCE BLOCKED ON MCP SESSION. The private plugin is selected and exposes four Workspace Shell actions, but new-chat runtime_inventory, git_head at expected 01a95b61410e2f427b9885a19e6a0b9c5ee60a38, and git-read rev-parse HEAD returned McpServerError: Session terminated without structured results/receipts. PR #573 comment 6564541283 records exact observations and operator-reported successful root authority/source split. FIRST diagnose the existing connector/tunnel/frontend transport using read-only evidence and restore session availability without rerunning activate_live.sh, reinstalling, recreating the tunnel, changing runtime API key, enabling units, or introducing privileged helpers. THEN perform full exact-SHA bounded positive/negative acceptance and read receipts. Do not resume PADataset v3 migration until acceptance passes.

## Remaining work

- Diagnose existing private Workspace Shell MCP session/transport reachability using read-only connector and host diagnostics; do not rerun activation, reinstall, recreate tunnel, replace runtime key, or broaden authority.
- Recover live runtime_inventory and inspect all four Workspace Shell unit states after the authority/source split.
- Perform exact-SHA Git observations and one successful bounded git-read execution using 01a95b61410e2f427b9885a19e6a0b9c5ee60a38, plus a source-verified allowed bounded validation.
- Read positive execution receipts and verify task binding, decision, exit code, privileged=false, hash-linkage where present, and secret minimization.
- Perform post-repair unauthorized path, credential, argv/shell, and empty-store privileged helper denial tests.
- Default to services remaining boot-disabled after acceptance unless a separate operational decision authorizes otherwise.
- After acceptance passes and evidence is persisted, resume the parked GitRunner migration at padataset-cpu-public-v1 with new exact canary authority, preserving GPU containment.

## Blockers / gates

- Workspace Shell transport is currently unavailable through the existing private ChatGPT plugin: fresh runtime_inventory, git_head, and bounded git-read calls all returned McpServerError: Session terminated (PR #573 comment 6564541283). Root cause unknown; do not conflate transport failure with authorization denial.
- Operator-reported authority/source split repair passed and binds the independent trusted authority root /etc/workspace-shell/authority to executable source 01a95b61410e2f427b9885a19e6a0b9c5ee60a38, but current executor has not reattested host state after the restart.
- Live positive bounded command/receipt acceptance and post-repair adversarial denials remain not run. Do not treat Workspace Shell as accepted Lambda transport until they pass.
- Workspace Shell systemd units remain intentionally boot-disabled per last operator report; do not enable them during this blocked acceptance.
- Privileged helper registry and operator trust stores remain empty/fail-closed; no privileged execution is authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
