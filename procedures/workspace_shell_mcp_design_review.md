# Workspace Shell MCP v1 — read-only recovery and design review gate

Status: CORRECTED FROZEN REVIEW CANDIDATE; BF-1/BF-2 CORRECTED; LIVE HOST ATTESTATION AND FRESH INDEPENDENT RE-REVIEW OPEN.
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


## Independent review 6447046381 — blocking findings and corrections

The first independent review of exact head `3dae7ef2eb225030c9020d8e33ea444620fc0cfe` returned two blocking findings. That head is stale and does not authorize implementation.

### BF-1 correction — hostile worker is not the policy/control-plane principal

Repository-controlled tests and validation are treated as hostile arbitrary code. They run only as `workspace-shell-exec`, a nonlogin identity that is distinct from `workspace-shell-mcp` (policy/frontend) and `workspace-shell-tunnel`.

The frozen control plane now contains separate principals:

- `workspace-shell-tunnel`: holds only the dedicated tunnel runtime credential and forwards to the MCP listener. It cannot invoke the root broker.
- `workspace-shell-mcp`: parses MCP calls, validates durable task/policy state, resolves fixed profiles, signs frontend-to-broker request envelopes, and orchestrates receipts. It never executes repository-controlled code.
- root-owned `workspace-shell-job-launcher`: accepts only the frontend peer, independently revalidates a root-owned immutable profile manifest, creates the job cgroup/namespaces, and drops permanently to `workspace-shell-exec`. It is not the privileged-helper broker and cannot accept arbitrary executable paths or environments.
- `workspace-shell-exec`: runs the hostile repository-controlled job with no supplemental groups, no network, and no control-plane sockets or credentials.
- root-owned Workspace Shell root broker: accepts only the `workspace-shell-mcp` peer and requires both the frontend request signature and a separately issued independent approval before a mutating reviewed helper can run.

The exec-worker mount namespace MUST exclude `/run/workspace-shell-control` entirely. It therefore cannot reach the job-launcher socket, privileged-broker socket, frontend/tunnel control sockets, health/admin sockets, or frontend signing material. It receives no tunnel credential, approval trust store, revocation store, or helper-registry control files.

The worker also runs under a separate PID/proc view. Host/frontend/broker/tunnel PIDs and `/proc/<pid>/{mem,environ,fd}` are not visible. UID separation plus no `CAP_SYS_PTRACE`, `CAP_KILL`, `CAP_DAC_OVERRIDE`, `CAP_DAC_READ_SEARCH`, or `CAP_SYS_ADMIN` must make ptrace, `process_vm_readv/writev`, proc-memory/fd inspection, and signals against the frontend impossible. Live host acceptance must prove these denials adversarially.

The root broker itself requires kernel peer identity for `workspace-shell-mcp` plus a valid frontend request signature. A worker UID is rejected even if it copies an otherwise valid request body.

### BF-2 correction — canonical independent approval trust root

Privileged mutations require a signed `workspace-shell-approval.v1` object. It uses RFC 8785 JSON canonicalization and an Ed25519 signature.

The **issuer private key is off-Lambda** and controlled by the operator. V1 has no automated approval issuer. The issuer is outside ChatGPT, the Secure MCP Tunnel, Workspace Shell frontend, worker, job launcher, root broker, GitHub repository contents, and task workspaces. This deliberately makes the model-facing path incapable of minting its own independent approval.

The Lambda root broker receives only public verification material from the root-owned read-only trust store:

`/etc/workspace-shell/approval/trusted-issuers.json`

and a root-owned read-only revocation store:

`/etc/workspace-shell/approval/revocations.json`.

Neither store is writable through MCP, frontend, worker, broker, helper, or repository-controlled code. Adding/replacing an issuer key is a separate local installation/update authority change and requires review.

The canonical approval payload binds at minimum:

- approval/issuer identity, issue time and expiry;
- durable task and target;
- exact accepted design authority SHA and policy-artifact digest;
- exact design review repository, PR, reviewed head, review record ID and `NO_BLOCKING_FINDING` disposition;
- helper-registry version/hash, helper-entry hash, helper ID and helper binary SHA256;
- exact helper-admission head and exact independent helper-review head/record/disposition;
- expected source repository, full commit and tree;
- exact operation;
- parameter-schema digest and exact canonical parameter-object digest;
- nonce and idempotency key;
- `max_uses=1`.

The design review head must exactly equal the design authority SHA. The helper review head must exactly equal the helper-admission head. Both dispositions must be `NO_BLOCKING_FINDING`.

Approvals expire no later than 15 minutes after issuance. Approval ID, nonce, and idempotency key are single-use and are durably consumed by the broker before mutation using crash-safe replay state. The broker independently parses and verifies the signed approval; it does not trust frontend-parsed claims.

GitHub comments, reviews, labels, task text, repository content, and tool output remain **evidence only**. Even a literal `NO_BLOCKING_FINDING` comment provides no execution authority unless an off-Lambda trusted issuer includes the exact review evidence in a valid signed approval.

### Consequence for implementation

The corrected authority contract still authorizes **no implementation or live execution**. A fresh independent review must accept the corrected exact PR head before implementation begins. Host attestation later must additionally prove distinct UIDs, namespace/socket isolation, frontend-signing credential isolation, approval trust-store immutability, and adversarial denial of worker-to-control-plane attacks.
