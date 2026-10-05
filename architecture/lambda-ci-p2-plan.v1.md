# Lambda CI P2 Plan v1

Status: implementation candidate for the authorized P2 gate.

## P2 objective

Create the first real research-engine execution identity and prove that a
one-job JIT runner can execute on Lambda without gaining unrelated host,
project, production-service, Docker, or GPU authority.

P2 is intentionally split:

### P2-A — root preflight + bootstrap

Run root-only transient probes **before persistent host mutation**:

1. snapshot nftables/iptables/UFW state without changing it;
2. prove the candidate systemd process/filesystem hardening starts cleanly;
3. prove cgroup-BPF network policy still permits DNS/public GitHub egress while
   blocking loopback, Tailscale/CGNAT, RFC1918/link-local, and the host's
   directly connected campus subnet;
4. prove `DevicePolicy=closed` denies NVIDIA access;
5. prove an explicitly granted GPU0 device set can be observed without exposing
   GPU1.

Only if those probes pass may bootstrap create:

- `ci-controller` (unprivileged GitHub-facing controller identity);
- `ci-research-engine` (project job identity);
- `/srv/workspace-ci/research-engine/*` project roots;
- root-owned read-only Actions runner base `v2.337.0`;
- root-owned kill-switch command.

No GitHub runner is registered in P2-A.

### P2-B — first JIT no-op runner

Use GitHub's repository JIT runner API as a bootstrap-only credential path.
GitHub documents that the endpoint creates a configuration for a one-job runner
and requires repository Administration:write for a fine-grained token (or repo
scope for a classic PAT).

The admin credential is used only to mint the encoded JIT configuration. It is
never passed into the job environment or root provisioner.

The encoded JIT config is then piped to the root launcher over stdin and supplied
to the runner only as `ACTIONS_RUNNER_INPUT_JITCONFIG`.

The no-op workflow is trusted/default-branch controlled and targets labels:

- `self-hosted`
- `lambda-research-engine`
- `cpu-test`

The runner executes one receipt job, uploads evidence, exits, and is removed.

## Filesystem decision from P1 receipt

`/srv` is ext4 on the production root filesystem and quota tooling is absent.
P2 therefore does **not** remount the root filesystem or enable filesystem
quotas. Job scratch remains bounded operationally by one-job concurrency,
runtime/resource limits, free-space guards, and mandatory cleanup.

A stronger fixed-size scratch filesystem may be added before heavy P3/P4 jobs if
measured disk pressure requires it.

## Network policy

The host uses a local DNS stub, a public campus subnet, Tailscale, Docker
bridges, and production PostgreSQL listening on wildcard addresses.

P2 uses systemd cgroup-BPF address controls. Access rules permit DNS resolution
and public Internet/GitHub egress while denying:

- localhost except the DNS stub allowance;
- RFC1918 networks;
- CGNAT/Tailscale `100.64.0.0/10`;
- IPv4/IPv6 link-local;
- IPv6 ULA;
- the host's directly connected IPv4 subnet.

The root preflight verifies denial against live Lambda endpoints before any
persistent user/runner mutation.

## GPU policy

P2 is CPU-only. The device preflight proves that GPU access is denied by default.
A narrow GPU0 allow probe is diagnostic evidence for the later P4 profile, not a
grant to P2 jobs.

## Credential boundary

P2-B may use a one-time administrator credential only to mint the JIT payload.
The final steady-state design still uses the pinned `actions/scaleset` client
behind `ci-controller`; P2-B does not substitute a long-lived personal
credential for that controller.

## Fail-closed rules

Any failed transient probe stops before `useradd`.

Any failed post-bootstrap identity isolation check blocks P2-B.

No script in P2:

- adds a CI user to sudo or Docker groups;
- edits nftables/iptables/UFW rules;
- starts/stops research-engine production services;
- touches the production database;
- registers a persistent runner;
- writes GitHub credentials to disk.
