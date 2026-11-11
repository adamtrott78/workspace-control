# Canonical ChatGPT Plugin Edit / Reinstall Workflow

Status: **CANONICAL for private App-backed MCP plugins in this workspace**

This procedure records the proven ChatGPT-side workflow used for Workspace Shell on 2026-11-10. Use the same pattern for Workspace Shell, Heartbeat, and other owned private MCP apps unless a later validated procedure explicitly supersedes it.

## Invariant

Changing only the MCP server implementation does not require creating a new ChatGPT app identity. Changing the MCP **tool schema** does require ChatGPT to rediscover the server's tools. The authoritative app identity must be preserved; do not create duplicate private apps just to refresh tools.

## Required order

1. **Implement and validate the server change first.**
   - Freeze an exact source SHA.
   - Run the repository/security contract suite.
   - Do not touch the installed ChatGPT app while the candidate server is unvalidated.

2. **Deploy the exact validated server candidate.**
   - Preserve endpoint, tunnel identity, certificates, and existing app binding unless the change explicitly requires otherwise.
   - Verify the MCP frontend and tunnel are healthy before attempting ChatGPT-side discovery.
   - A healthy tunnel is insufficient if the MCP frontend is crash-looping.

3. **For a tool-schema change, refresh the existing private app rather than creating a new identity.**
   - Preferred first action when the MCP frontend is healthy: **Manage -> Refresh tools**.
   - If a clean reinstall is desired or Refresh tools is unavailable/stale:
     1. Explicitly uninstall the existing ChatGPT plugin/app registration.
     2. Resolve the already-owned private plugin by its existing backend identity.
     3. Surface the existing plugin through ChatGPT's install-card workflow.
     4. The user clicks **Install**. Installation remains a user approval boundary.
     5. Refresh the browser so ChatGPT reloads the registered tool set.
     6. If the schema changed, use **Manage -> Refresh tools** once the MCP frontend is healthy.
   - Do **not** use Plugin Creator package updates to change an App-backed MCP binding or action schema. App-backed plugin package updates preserve the App configuration/bindings; MCP actions are refreshed from the App/server discovery path.

4. **Verify from the model-visible tool contract.**
   - Inspect the registered tool descriptions/schemas, not just the app UI.
   - For Workspace Shell, verify expected target/profile enums before any research execution.
   - A visible app with stale tool enums is not accepted as refreshed.

5. **Only then resume task execution.**
   - Run one read-only acceptance call first.
   - Record exact server SHA, app/tool refresh evidence, and the first successful receipt.

## Failure interpretation

- **Refresh tools -> "Couldn't update the app"** means tool discovery failed. Treat the MCP frontend/tunnel path as the first diagnostic target.
- If the tunnel is active but the MCP frontend is `activating (auto-restart)` / exit-code, diagnose the MCP frontend crash first. Reinstalling the app again cannot fix a dead server.
- If a direct app call returns `Session terminated`, do not infer that the ChatGPT app itself is corrupt; correlate with service state.
- Do not repeatedly uninstall/reinstall while the server is unhealthy.

## Proven Workspace Shell example

The 2026-11-10 Workspace Shell multirepo upgrade demonstrated the intended flow:

- validated and deployed Workspace Shell candidate;
- preserved the existing private App identity;
- explicitly uninstalled the old ChatGPT registration;
- surfaced the same owned private Workspace Shell plugin through the ChatGPT install card;
- user approved installation;
- browser refresh reloaded the app UI;
- tool refresh then exposed the true remaining blocker: the MCP frontend was crash-looping while the secure tunnel remained active.

This sequence is the default operator procedure for future private-plugin edits unless superseded by a newer validated runbook.
