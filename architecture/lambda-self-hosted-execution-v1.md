# Lambda Self-Hosted Execution v1

Status: **DESIGN CANDIDATE — NO RUNNER INSTALLED**

Owning task:

`tasks/active/workspace-lambda-self-hosted-execution-v1.json`

## Purpose

Create a project-isolated GitHub Actions execution lane on the existing Lambda
workstation so ChatGPT can iterate through:

```text
Git branch mutation
→ trusted GitHub trigger
→ Lambda execution on the real target hardware/environment
→ GitHub check/log/artifact evidence
→ ChatGPT diagnosis/revision
→ rerun
```

without routine human SSH mediation.

This capability is intended for software-engineering validation, hardware/model
benchmarks, and environment-specific integration tests. It is **not** permission
for arbitrary unrestricted access to the Lambda host.

Existing GitHub-hosted CI remains the known-good control and is not replaced by
this design.

## Why this is worth doing

The current GitHub-hosted CI path is excellent for cheap deterministic checks,
but runner allocation has repeatedly added multi-minute queue delays even when
the actual job completes quickly.

The existing research-engine CI does not load heavyweight models. It installs the
package, compiles, runs pytest with PostgreSQL, validates Compose, and builds the
daemon image. Heavyweight model/runtime work has already been executed on Lambda.

A Lambda-backed Actions lane therefore solves two separate problems:

1. eliminate dependence on GitHub-hosted runner allocation for selected jobs;
2. let project code execute in the same hardware/software environment it is
   designed to use, including the RTX A4500 GPUs.

The second benefit is more important: the same executor that writes code can
receive concrete Lambda logs/artifacts, revise the branch, and rerun without a
human terminal relay.

## External platform facts

Current GitHub documentation establishes the following:

- self-hosted runners may be repository-, organization-, or enterprise-scoped;
- repository-level runners are dedicated to one repository;
- self-hosted runner compute is free from GitHub Actions billing; the runner
  owner pays/maintains the machine;
- GitHub explicitly warns that persistent self-hosted runners do not receive the
  clean-VM guarantee of GitHub-hosted runners and may remain compromised after
  untrusted workflow execution;
- ephemeral runners registered with `--ephemeral` automatically de-register
  after one job;
- GitHub also supports one-job just-in-time runner configurations through the
  REST API;
- GitHub recommends externally preserving ephemeral-runner diagnostic logs;
- repository runner registration/JIT APIs can use fine-grained tokens or GitHub
  App tokens and require repository Administration write permission;
- workflow `GITHUB_TOKEN` permissions can be reduced to read-only or disabled
  per job;
- `workflow_dispatch` definitions must exist on the default branch;
- self-hosted runner job-start/job-complete hooks are available, but machine
  destruction after a job must be handled outside the job-complete hook.

Primary references:

- https://docs.github.com/en/actions/concepts/runners/self-hosted-runners
- https://docs.github.com/en/actions/reference/runners/self-hosted-runners
- https://docs.github.com/en/actions/reference/security/secure-use
- https://docs.github.com/en/rest/actions/self-hosted-runners
- https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/run-scripts
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## Threat model

The design assumes AI-generated project code can be defective and should be
treated as potentially destructive even when it is not intentionally malicious.

### Host threats

A job must not be able to:

- run as the normal `atrott` login account;
- read personal SSH keys, shell history, browser/application credentials, or
  unrelated home-directory content;
- use sudo;
- access a Docker daemon/socket or otherwise acquire root-equivalent host
  authority;
- edit root-owned runner/controller configuration;
- signal or control processes owned by other project/users;
- survive after its job cgroup is terminated;
- modify system files, kernel settings, modules, clocks, cgroups, or device
  policy;
- access unrelated project workspaces or caches.

### Project threats

A research-engine job must not be able to:

- read/write PADataset, course repositories, workspace-control state, or another
  project's runner workspace;
- mutate the production research-engine database;
- control the production daemon or its systemd user unit;
- reuse stale mutable build state from a previous job without an explicit cache
  contract;
- silently change the trusted Lambda workflow/controller used to execute it.

### GitHub threats

A job must not receive:

- personal Git credentials;
- the controller's runner-registration credential;
- broad repository write permissions;
- arbitrary repository/organization secrets.

A candidate branch must not be able to rewrite the trusted workflow that grants
Lambda execution.

### Resource threats

A job must not be able to:

- consume unbounded RAM/CPU/processes/runtime;
- run arbitrary concurrent GPU jobs that collide with another accepted owner;
- leave model-server or worker processes behind after completion;
- fill the disk indefinitely through cache/scratch growth.

## Architecture alternatives considered

### A. Persistent runner under the normal login user

**Rejected.**

It would expose unrelated repositories, credentials, production state, and
normal-user processes to every workflow.

### B. Persistent project runner under a dedicated Unix user

**Viable but not preferred.**

It provides strong cross-project filesystem separation, but the runner
registration state and mutable work directory persist across jobs. A compromised
job can poison later jobs and can potentially access long-lived runner
credentials.

### C. Docker-hosted runner with access to `/var/run/docker.sock`

**Rejected.**

Docker socket/group access is effectively root-equivalent host authority.

### D. Disposable VM/microVM per job

**Strongest isolation, poor pilot fit.**

This provides excellent cleanliness but adds substantial setup complexity and
GPU passthrough problems for the existing dual RTX A4500 workstation.

### E. Rootless container per job

**Promising second-stage hardening, deferred.**

It improves filesystem/process isolation but introduces additional complexity for
CUDA/NVIDIA access and Actions/service-container compatibility. It should be
considered only if the native systemd sandbox is insufficient.

### F. Privilege-separated scale-set listener + narrow root provisioner + one-job repository-scoped runner + dedicated project identity + systemd sandbox

**Selected for the pilot after external research.**

GitHub's official Runner Scale Set Client owns the Actions polling/session/JIT protocol in an unprivileged `ci-controller`. A separate root-owned local provisioner holds no GitHub credentials and may only instantiate root-owned allow-listed project/profile sandbox templates. This gives strong practical isolation while retaining native GPU access and avoiding Docker/root-equivalent workflow permissions.

## Selected topology

```text
GitHub private repository
        │
        │ trusted default-branch workflow event
        ▼
queued Lambda job
        │
        ▼
ci-controller (unprivileged)
GitHub Runner Scale Set Client
        │
        ├─ owns repo-scoped GitHub App credential
        ├─ receives scale-set demand / JIT runner config
        └─ cannot access project/home/root authority
        │
        ▼
workspace-ci-provisioner (root, local-only)
        │
        ├─ owns NO GitHub credential
        ├─ validates root-owned project/profile manifest
        ├─ creates fresh one-job runner directory
        └─ launches dedicated project UID in hardened systemd cgroup
        ▼
ci-research-engine
        │
        ├─ fresh work tree
        ├─ project-only writable cache
        ├─ selected GPU device(s)
        ├─ public Internet egress
        ├─ no normal /home
        ├─ no sudo
        ├─ no Docker socket
        ├─ no production localhost/private-network access
        └─ read-only GitHub token only
        │
        ▼
job completes / artifacts upload
        │
        ▼
runner automatically deregisters
        │
        ├─ controller preserves runner diagnostics
        ├─ kills entire transient cgroup
        ├─ verifies no owned process/model leak
        └─ destroys work/config directory
```

The unprivileged scale-set listener requests the next runner; the narrow root provisioner instantiates only an allow-listed sandbox. After acceptance, `minRunners=1` may be evaluated for active projects to remove cold-start latency, while every runner still executes only one job.

## Trigger model

### Requirement

The candidate branch must not control the trusted Lambda workflow.

### Preferred trigger

Use a workflow stored only on the default branch and triggered by a PR
conversation command such as:

```text
/lambda-ci <exact-head-sha> <profile>
```

The existing GitHub connector can create PR conversation comments, making this
trigger available to ChatGPT without human UI interaction.

The default-branch workflow must:

1. run only for a private same-repository PR;
2. require a trusted actor/owner association;
3. parse the exact requested commit SHA/profile;
4. resolve the current PR head and require exact SHA equality;
5. set `permissions: contents: read` (all unspecified permissions become none);
6. use no project secrets in the pilot;
7. check out the requested SHA with `persist-credentials: false`;
8. execute only an allow-listed validation profile;
9. upload structured logs/reports/artifacts;
10. never push/commit from the runner.

The workflow definition used for the Lambda lane must not come from the candidate
branch.

### Why not ordinary PR workflow YAML from the candidate branch?

A normal branch-controlled workflow would let candidate code alter the execution
policy itself. The trusted control workflow must remain on the protected/default
branch and treat the candidate SHA as data.

## Controller credential model

The controller and job runner use **different credentials**.

### GitHub listener

Run a pinned version of GitHub's official `actions/scaleset` client as an
unprivileged `ci-controller` identity. The listener owns the repository-scoped
GitHub credential and JIT/scale-set protocol, but cannot launch arbitrary root
commands or read project/home/production data.

Preferred credential: a private GitHub App installed only on explicitly opted-in
repositories and exchanging for short-lived installation tokens.

Pilot fallback: a narrowly scoped fine-grained PAT only if GitHub App bring-up
blocks the first controlled test.

### Root provisioner

A separate root-owned local-only provisioner holds **no GitHub credential**.
It accepts only a structured, allow-listed project/profile/JIT request from the
controller, validates it against a root-owned manifest, creates the transient
runner workspace, and launches the systemd sandbox under the project UID.

The root provisioner is deliberately not a general command executor.

### Job

The workflow job receives only GitHub's per-job `GITHUB_TOKEN` with:

```yaml
permissions:
  contents: read
```

Candidate programs do not receive the token as an environment variable.

Checkout uses:

```yaml
persist-credentials: false
```

No repository secrets are exposed during the pilot.

## Runner lifecycle

### Preferred

Use a JIT one-job runner when repository-level JIT configuration is validated
against the user's repository/account topology.

### Fallback

Use a repository registration token plus:

```text
config.sh --unattended --ephemeral ...
```

GitHub automatically de-registers an ephemeral runner after one job.

### Cleanliness

Every job gets a newly created runner/work directory. After the runner exits:

1. copy `_diag` logs to a root-controlled diagnostic archive;
2. stop/kill the whole transient systemd cgroup;
3. verify no project UID processes remain;
4. verify no assigned-GPU processes remain;
5. delete the runner configuration and work directory;
6. leave only explicitly allowed project caches/artifacts.

No previous checkout survives as mutable state.

## Per-project identity model

Initial research-engine identity:

```text
user:      ci-research-engine
work root: /srv/workspace-ci/research-engine/jobs
cache:     /srv/workspace-ci/research-engine/cache
logs:      /srv/workspace-ci/research-engine/logs
```

Future projects receive separate identities:

```text
ci-padataset
ci-mth602
ci-cis560
...
```

A project UID is not a member of another project group and receives no ACL for
another project root.

Do not run one unrestricted multi-repository runner account.

## systemd sandbox policy

The transient job unit should begin from this policy family, with each option
validated on Lambda before promotion:

```text
User=ci-research-engine
Group=ci-research-engine

NoNewPrivileges=yes
CapabilityBoundingSet=
RestrictSUIDSGID=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectClock=yes
ProtectHostname=yes
RestrictRealtime=yes
UMask=0077

ReadWritePaths=/srv/workspace-ci/research-engine/jobs
ReadWritePaths=/srv/workspace-ci/research-engine/cache

KillMode=control-group
SendSIGKILL=yes
TimeoutStopSec=<bounded>
RuntimeMaxSec=<profile-specific>

MemoryMax=<profile-specific>
TasksMax=<profile-specific>
CPUQuota=<profile-specific>
```

Candidate hardening options that require a Lambda compatibility probe:

- `ProtectProc=invisible`;
- `ProcSubset=pid`;
- `DevicePolicy=closed` plus only the required NVIDIA device files;
- `IPAddressDeny` rules blocking loopback/private/Tailscale destinations while
  preserving DNS and public egress.

Do **not** use `MemoryDenyWriteExecute=yes` without proof because JIT/ML
runtimes may require executable memory.

Do not use aggressive syscall filtering until Python/CUDA/model runtimes have
been characterized.

## Network boundary

The job needs outbound access to GitHub and, for some profiles, PyPI/Hugging
Face/other public package/model sources.

It should not have network reachability to:

- the production PostgreSQL listener;
- research-engine daemon/broker local ports;
- local development services;
- Tailscale peers;
- private LAN/campus services.

Preferred policy:

- allow public Internet egress;
- allow only the DNS resolver needed by the host;
- deny loopback except DNS;
- deny RFC1918/private, link-local, and Tailscale ranges.

This must be validated on the actual Lambda network before enforcement.

## Production database boundary

The pilot never uses the production database.

For ordinary research-engine tests, prefer one of:

1. an ephemeral PostgreSQL cluster owned by `ci-research-engine` under the job
   directory using a Unix socket;
2. a later rootless-containerized service after that path is separately
   validated.

The production PostgreSQL credentials/port are not part of the CI environment.

## GPU policy

The pilot begins with one Lambda job at a time.

Before each GPU profile:

1. assert the selected GPU allocation policy;
2. verify no conflicting accepted owner is using the target GPU;
3. expose only the selected device(s) when the systemd/NVIDIA device policy is
   proven;
4. record baseline VRAM/process state;
5. run the bounded benchmark/test;
6. terminate the full cgroup;
7. verify no GPU process leak.

GPU access is a resource grant, not repository authority.

## Cache policy

Caches are performance aids, never sources of truth.

Pilot:

- workspaces are always ephemeral;
- candidate jobs receive only ephemeral writable cache/download staging;
- long-lived executable/model dependency caches are written or promoted only by
  trusted cache-management/default-branch operations;
- promoted caches are mounted read-only into candidate jobs;
- cache identities include immutable dependency/model/runtime identities;
- jobs must tolerate cache miss/rebuild;
- no project can modify another project's cache.

Hugging Face already uses revision snapshots backed by hashed blobs; later a
trusted cache manager can exploit that layout for deduplicated read-only model
snapshots across projects without granting candidate jobs write access.

Do not bind the normal user's writable model cache into a job and do not trust
candidate-written persistent cache state.

## Resource profiles

The trusted workflow chooses from an allow-listed profile. Candidate code does
not choose arbitrary host privileges.

Example profiles:

### `cpu-test`

- no GPU;
- bounded CPU/RAM/runtime;
- ephemeral project database allowed;
- public package egress allowed.

### `gpu-small`

- one explicitly selected GPU;
- bounded CPU/RAM/runtime;
- project cache;
- no production services.

### `gpu-heavy`

- separately authorized;
- larger memory/runtime envelope;
- may use both GPUs only when the owning task explicitly requires it;
- always emits resource/process receipts.

### `production-acceptance`

Not part of the initial pilot.

This later profile would need a different, explicitly reviewed authority model
because production acceptance may intentionally inspect/start real services.

## Closed-loop ChatGPT workflow

Once the pilot is accepted, the normal path becomes:

```text
1. ChatGPT reads durable task/project state.
2. ChatGPT creates/updates an isolated Git branch/PR.
3. ChatGPT posts:
      /lambda-ci <head-sha> <profile>
4. Trusted default-branch workflow queues a Lambda job.
5. Controller presents a fresh ephemeral repo-scoped runner.
6. Lambda executes the exact branch SHA.
7. GitHub receives PASS/FAIL logs and structured artifacts.
8. ChatGPT reads the run/jobs/artifacts using the GitHub connector.
9. On failure:
      inspect evidence
      → bounded code fix
      → new head SHA
      → repeat
10. On pass:
      normal review/merge/checkpoint procedure continues.
```

The current GitHub connector already supports:

- branch/file/PR mutations;
- PR conversation comments;
- workflow-run/job inspection;
- workflow artifact listing;
- workflow artifact download;
- rerunning failed/cancelled jobs.

Therefore the connector side of the closed loop already exists.

## What this does and does not guarantee

Lambda-backed validation can provide dramatically stronger confidence that code
works in the actual target environment, because tests execute against the real
OS, installed drivers, CUDA stack, filesystems, CPUs/GPUs, and project runtime.

It cannot mathematically guarantee all future executions are error-free.
Nondeterminism, external services, race conditions, changing data, hardware
faults, and untested paths remain possible.

The correct goal is:

> every accepted implementation must have direct execution evidence from the
> environment it claims to support, at the appropriate validation tier.

## Pilot sequence

### P0 — Host probe, no mutation beyond diagnostics

Collect:

- distro/kernel/systemd version;
- cgroup v2 status;
- systemd sandbox feature availability;
- current GPU device nodes and permissions;
- free disk and target `/srv` filesystem;
- DNS resolver topology;
- production localhost/private-network listeners relevant to denial rules;
- existing users/groups;
- GitHub runner binary prerequisites.

### P1 — Root-owned bootstrap artifacts

Create reviewed scripts/config only:

- project manifest;
- dedicated user/root directory setup;
- controller configuration;
- systemd controller template;
- systemd transient job sandbox profile;
- kill-switch/remove script.

No real GitHub registration until static review passes.

### P2 — Dedicated project user and no-op runner

One-time human/root bootstrap creates `ci-research-engine`.

Acceptance tests must prove the user cannot:

- read `/home/atrott`;
- read another project root;
- use sudo;
- access Docker socket;
- access production database/daemon endpoints;
- write system locations.

Then register one one-job runner and execute a no-op receipt job.

### P3 — CPU project validation

Run a candidate research-engine branch through:

- checkout;
- ephemeral venv;
- compile/static tests;
- unit tests using an ephemeral CI database;
- artifact upload.

No GPU yet.

### P4 — GPU validation

Run a bounded non-scientific CUDA/model allocation probe, then one existing
project hardware benchmark under the sandbox.

Require clean post-job GPU/process state.

### P5 — Closed-loop acceptance

ChatGPT itself:

- makes a bounded branch change;
- triggers Lambda validation through GitHub;
- receives a deliberately failing result;
- diagnoses/fixes it;
- reruns;
- receives PASS;
- consumes an uploaded artifact;
- completes without human SSH.

This is the decisive acceptance test.

### P6 — Cross-project isolation

Opt in a second project (recommended PADataset) under a second UID/root/cache.

Deliberately test that each project cannot read/write the other's workspace or
cache.

## Kill switch

The system must have a simple root-owned kill switch that:

1. stops the project controller;
2. kills all runner/job cgroups;
3. deregisters or allows any ephemeral runner to expire;
4. preserves diagnostic logs;
5. leaves project source repositories and production services untouched.

Human SSH remains the break-glass path until this kill switch is validated.

## Promotion decision

The pilot may proceed to host bootstrap only if all of the following hold:

- project-specific UID/workspace design is accepted;
- controller credentials are isolated from job code;
- runner is one-job/ephemeral;
- trusted workflow is not candidate-controlled;
- no sudo/Docker socket/personal credentials are exposed;
- production service/network denial plan is testable;
- project cleanup/resource limits/kill switch are explicit;
- existing GitHub-hosted CI remains available as rollback/control.

## Deferred improvements

Do not implement these before the research-engine pilot proves the basic model:

- organization-wide runner groups;
- rootless container layer;
- multi-GPU concurrent scheduling;
- cross-project shared writable model cache;
- automatic production-acceptance authority;
- public-repository jobs;
- arbitrary workflow-defined privilege/resource profiles;
- migration of every workspace project at once.


## Evidence-first research revision

The initial design was re-evaluated using the workspace evidence-first research
method before host mutation.

The resulting survey is recorded in:

`architecture/lambda-self-hosted-execution-research.v1.md`

Material changes from the initial candidate:

- use GitHub's official pinned Runner Scale Set Client instead of hand-rolled
  GitHub queue/JIT polling;
- split the unprivileged GitHub listener from the root provisioner;
- make long-lived model/dependency caches trusted-write/read-only-to-jobs rather
  than candidate-writable;
- treat the issue-comment trigger explicitly as a pwn-request boundary with no
  secrets and a read-only job token;
- retain native systemd/cgroup-v2 isolation for the first pilot while keeping
  rootless Podman + NVIDIA CDI as a later hardening option.
