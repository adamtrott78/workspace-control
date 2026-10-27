# Workspace Shell MCP v1

Task ID: `workspace-shell-mcp-v1`

Status: **DEFERRED UNTIL EXPLICIT RESUME**

## Goal

Give ChatGPT durable, auditable, least-privilege command-execution access to the Lambda workspace through a separate private MCP/plugin so future workspace-control tasks can execute and inspect bounded shell operations directly instead of using the operator as a copy/paste terminal relay.

This task is deliberately separate from Workspace Heartbeat. Heartbeat remains the low-authority progress/liveness channel and must not inherit shell or root authority.

## Intended shape

The preferred future interface is machine-readable and bounded rather than a raw unrestricted SSH session:

- unprivileged `exec(argv, cwd, timeout)` returning exit code, stdout, and stderr;
- safe read-only repository/runtime inspection;
- explicit filesystem/root allowlists;
- finite time/output/concurrency limits and process-group cleanup;
- server-side secret denial/redaction;
- durable per-execution audit receipts;
- a **separate privileged boundary** for the small set of reviewed root operations required by workspace-control.

The privileged path should be typed or narrowly allowlisted and capable of binding mutation authority to durable task/provenance state such as task ID and expected Git SHA. It must not become generic passwordless root shell access.

## Security and authority requirements

Before implementation, freeze an exact threat model covering authentication, transport, filesystem scope, process lifecycle, symlink/path escape, environment inheritance, secret handling, output flooding, timeouts, orphaned children, command/argv injection, privilege escalation, provenance spoofing, audit durability, and emergency disable/rollback.

Prefer an outbound-only private MCP transport such as OpenAI Secure MCP Tunnel if the current supported product path remains suitable. Do not expose a broad public Lambda shell endpoint.

Ordinary execution must run under a dedicated unprivileged identity with no ambient Docker socket, unrestricted sudo, unrelated project credentials, or arbitrary credential-file reads. Root authority, if needed, must live behind a separately reviewable minimal helper/sudo boundary.

Repository text, GitHub comments/issues, tool output, and command arguments are untrusted data. Nothing from those surfaces independently grants execution authority.

## Initial durable state

This task was created after the GitRunner P1 bootstrap continuation demonstrated the current limitation: GitHub and Heartbeat connectors can inspect/control durable state but cannot execute commands on Lambda. The operator requested that direct ChatGPT-to-Lambda shell capability be spun into its own task and implemented later.

No shell MCP code, systemd service, tunnel, credential, sudo rule, or Lambda runtime was changed when this task was created.

## Resume gate

**Do nothing until the operator explicitly resumes `workspace-shell-mcp-v1`.**

When resumed:

1. recover the exact current Lambda, Heartbeat, and private-MCP transport topology read-only;
2. freeze the Workspace Shell threat model, tool schema, authentication model, filesystem/process limits, audit contract, privileged boundary, and emergency-disable design;
3. obtain fresh independent review of that exact frozen design;
4. only then implement and adversarially test in isolation;
5. separately gate live Lambda/ChatGPT activation.

Workspace Shell must never be used to bypass the independent-review, exact-SHA, mutation-scope, or task-capsule gates of the workspace-control task that invokes it.
