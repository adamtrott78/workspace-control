# Workspace Shell MCP v1 — read-only recovery and design review gate

Status: FROZEN REVIEW CANDIDATE; LIVE HOST ATTESTATION AND INDEPENDENT REVIEW OPEN.
Authority: `architecture/workspace-shell-mcp-authority-v1.json`; task capsule `tasks/active/workspace-shell-mcp-v1.json`.
Source Git main: `8a71aa3c60a4a0f230bcbee9711d2af79828c869`.
No Lambda changes, Heartbeat changes, endpoint creation, tunnel creation, or systemd changes authorized.

## Evidence recovered from GitHub
- Completed Workspace Heartbeat tunnel task documents deployed v0.4.8 `def7c5fe6498b1bd742d912c1490d1f7160cab5f`, localhost MCP `127.0.0.1:8787/mcp`, separate outbound Secure MCP Tunnel and v0.4.7/ngrok rollback at `/home/atrott/bin/heartbeat-rollback-v047-ngrok`.
- Heartbeat tunnel client implementation snapshot references version 0.0.18+, isolated tmux session `workspace-heartbeat`, user-owned runtime under `/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v048`. Those are prior documented deployment facts, NOT fresh process attestations.
- Workspace CI source service definitions place system maintenance authority behind `workspace-ci-maintenance.service` (root, restricted capabilities), plus `ci-maintenance` controller and separate `ci-controller`; `/run/workspace-ci`, `/var/lib/workspace-ci` and `/opt/workspace-ci` have distinct operational roles.
- Current control-plane task describes workspace-control CPU as not activated after observation-only diagnose; activation still requires independent review. The prospective shell may not invoke activation to bypass it.
- Historical operator home workspace checkout: `/home/atrott/adamArchives/Adam/workspace-control`. Shell exec identity SHALL NOT mount that operator home; it uses a separately prepared read-only snapshot.

## Recovery gaps — required before any host-specific final approval
Read-only host evidence is needed for effective runtime PID/executable/source SHA; tmux parentage; listener and tunnel-process/config metadata without secret contents; service users/groups; socket owners and permissions; accepted CI units' effective configuration/status; mount and ACL graph; root helper version/API; host confinement primitives (namespaces/seccomp/AppArmor or SELinux/cgroup-BPF); exact source checkout and projects that must remain invisible; tunnel and network compartment isolation; out-of-band service termination path. Do not read secret values or request operator to paste them.

Use a separately reviewed read-only diagnostic workflow before deployment. GitHub access alone cannot attest live Lambda status; the existing GitHub and Heartbeat connectors have no unrestricted host command capability.

## Incidents informing acceptance
Manual terminal round-trips during P1/bootstrap included exact worktree checkout and SHA checks, source digest checking, test invocation, service/child status, maintenance-controller receipt inspection, socket readiness and rollback observations. The future shell should support *typed observation and isolated bounded execution* for these, **not** reproduce ad hoc sudo or direct root script execution.

## Threat model
Assume model prompt injection from issues, repository files, terminal output and argv; compromised test scripts; symlink and path races; exfiltration through output/network; inherited process credentials; root-helper confused deputy; audit spoofing; cancellation orphans; tunnel/app credential compromise; and sibling-project access. The deployment MUST be structured so an attacker controlling arbitrary argv or repository bytes still cannot read host secrets or modify unrelated resources. A simple cwd validator or argv array is insufficient. Default-deny all unspecified operations.

## Review freeze procedure
1. Capture host attestation and compare against the architecture artifact. Any material discrepancy requires a new design commit.
2. Verify JSON schema and task capsule/handoff synchronization, review allowed paths only and test adversarial policy harness in isolation where possible.
3. Anchor design review to immutable PR head; fresh independent reviewer issues `NO_BLOCKING_FINDING` or exact blocking findings.
4. Implement only after accepted design; run isolated tests with no tunnel or production root authority.
5. Independently review implementation, staging and explicit operator-controlled kill switch.
6. Only with separate activation authorization provision a new tunnel, credential, service and root boundary. Never modify or share the Heartbeat runtime, port, tunnel or credentials.

## Design safety controls
v1 exposes typed `inspect`, profile-bound `exec`, exact-registry `run_reviewed_helper`, and `receipt` tools. Profile grammar is fail-closed: no free-form generic process execution, network access, shell, interpreter, package manager or hooks. The root path can invoke only a helper already admitted under a separately reviewed exact registry entry; the MCP call cannot choose an executable/argv/environment. No live privileged workspace-control activation is implicitly granted. The dedicated process is nonlogin, no supplemental groups, mount/network isolated, has explicit source-only and scratch mounts, and is terminated by its cgroup on deadline or cancel. Ordinary exec never receives tunnel credentials.

## Local emergency operation
The operator, via separate local root authority, must be able to stop/mask the Workspace Shell systemd units, kill the cgroup, revoke its Secure MCP Tunnel runtime authorization, and verify no listener/socket or child remains. Such recovery must function when the remote service itself is down. The precise installed unit/tunnel identifiers will be independently frozen at deployment review.

No host commands were executed during this design recovery and no live state has been newly verified.

## 2026-10-27 pre-review hardening
Current OpenAI Secure MCP Tunnel documentation was rechecked before independent review. The documented absolute request deadline is 120 seconds and includes hosted queue time, so the v1 synchronous command ceiling is frozen at 90 seconds rather than 120 seconds. This leaves transport/queue margin and prevents a command timeout from colliding with the tunnel deadline.

The privileged design was also corrected from a staging-only RPC to `workspace_shell.run_reviewed_helper`. The root-owned registry, not the model call, selects the exact executable, helper digest, closed parameter schema, target/task scope, pre/postconditions, side effects and rollback contract. Registering a new helper is itself an authority change requiring separate exact-head review. Generic root argv, generic sudo, generic systemctl and self-expansion of the registry remain forbidden.

OpenAI tool annotations remain advisory selection/confirmation metadata. The server and root helper must independently enforce all task, provenance, path, credential, process and privilege checks.
