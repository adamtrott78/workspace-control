# Lambda Self-Hosted Execution — Evidence-First Architecture Research v1

Date: 2026-10-05

Owning task: `workspace-lambda-self-hosted-execution-v1`

Status: **SURVEY COMPLETE — DESIGN REFINEMENT REQUIRED BEFORE HOST MUTATION**

## Research question

How do mature self-hosted CI systems safely execute arbitrary project code on
valuable local infrastructure, and which patterns should be adopted for the
Lambda workstation so ChatGPT can drive a closed edit → execute → inspect →
revise loop without gaining unrestricted host authority?

## Source classes reviewed

Primary platform/security guidance:

- GitHub Actions self-hosted runners, ephemeral/JIT runners, compromised-runner
  guidance, token permissions, event semantics, ARC and Runner Scale Set Client;
- GitLab Runner self-managed security and autoscaling/ephemeral executor
  guidance;
- Buildkite self-hosted agent security, compartmentalization and ephemeral agent
  patterns;
- Ubuntu/systemd execution and cgroup-v2 resource-control documentation;
- NVIDIA Container Toolkit / CDI rootless GPU documentation;
- Hugging Face Hub cache design and content-addressed snapshot layout.

The academic search surface was also queried, but broad CI/CD-security searches
were substantially noisier and less directly actionable than current primary
platform/runtime documentation for this operational design. The architecture
decision therefore weights official implementation/security guidance most
heavily.

## External evidence

### 1. Ephemeral one-job execution is the dominant security pattern

GitHub explicitly recommends ephemeral self-hosted runners for autoscaling and
does not recommend persistent autoscaled runners. Ephemeral runners receive one
job and automatically de-register; GitHub additionally requires their diagnostic
logs to be preserved externally for production troubleshooting.

GitLab makes the same argument from the opposite direction: a non-ephemeral
runner that serves multiple projects materially increases cross-project
compromise risk. Its autoscaling guidance uses single-job instances
(`capacity=1`, `max_use_count=1`) specifically so one job cannot poison the
next instance.

Buildkite likewise supports persistent or ephemeral agents and recommends
expiring agents after a job in hardened deployments.

**Decision:** one-job JIT/ephemeral runners remain a hard requirement.

References:

- https://docs.github.com/en/actions/reference/runners/self-hosted-runners
- https://docs.gitlab.com/runner/security/
- https://docs.gitlab.com/runner/executors/docker_autoscaler/
- https://buildkite.com/docs/agent/self-hosted/security
- https://buildkite.com/docs/agent/self-hosted/aws/architecture/securing-your-setup

### 2. Do not hand-roll GitHub's autoscaling/JIT protocol

GitHub now publishes `actions/scaleset`, a standalone Runner Scale Set Client
extracted from Actions Runner Controller. It is explicitly intended for custom
autoscaling **outside Kubernetes**.

The client owns:

- runner scale-set registration;
- long-poll message sessions;
- message acknowledgement/redelivery semantics;
- current assigned/running-job statistics;
- JIT runner configuration generation;
- GitHub App/PAT token exchange and refresh.

Its runners are ephemeral by default.

The project is currently Public Preview: GitHub says the API is stable but
interfaces/examples may change.

**Decision:** replace the draft hand-rolled GitHub polling/JIT controller with a
pinned version of the official Runner Scale Set Client. Keep our custom code
focused on Lambda-specific provisioning, isolation, GPU/resource policy and
cleanup.

Pin the exact client version/commit and hide it behind a narrow local adapter so
preview-interface churn cannot spread into workspace-control contracts.

References:

- https://docs.github.com/en/actions/reference/runners/self-hosted-runners
- https://github.com/actions/scaleset

### 3. Separate the GitHub listener from root provisioning

ARC's architecture deliberately separates the controller/listener plane from the
ephemeral runner workload and recommends isolating runner workloads from
production workloads. Buildkite similarly recommends compartmentalizing agent
responsibilities.

Our first draft combined GitHub API credentials and root provisioning authority
in one root-owned controller. That is unnecessarily large privilege.

**Revised decision:** use three privilege tiers:

1. `ci-controller`
   - unprivileged;
   - runs pinned GitHub Runner Scale Set Client / listener;
   - owns only the per-repository GitHub App/PAT material required for runner
     scale-set control;
   - cannot read project source, `/home/atrott`, production state, or root
     provisioner internals.

2. `workspace-ci-provisioner`
   - tiny root-owned local service/helper;
   - **no GitHub credentials and no public network requirement**;
   - accepts only structured allow-listed requests such as
     `{project, profile, jit_config}`;
   - validates every project/profile/path/device/resource against a root-owned
     manifest;
   - launches/kills the systemd sandbox and performs post-job cleanup.

3. project runner UID (initially `ci-research-engine`)
   - receives one JIT config;
   - runs one job;
   - no controller credential;
   - no sudo/Docker/personal credentials/production authority;
   - workspace/config destroyed after the job.

This ensures compromise of project code does not expose controller credentials,
and compromise of the network-facing controller does not directly provide an
arbitrary root command primitive.

### 4. Default-branch comment trigger is viable, but must be treated as a
pwn-request boundary

GitHub's `issue_comment` event runs the workflow definition from the default
branch. That property is useful: the candidate PR cannot rewrite the trusted
Lambda workflow.

However, GitHub explicitly warns that `issue_comment`/`pull_request_target`
workflows that fetch and execute PR code are a classic "pwn request" shape when
the job has secrets or powerful credentials.

**Decision:** keep the PR-comment trigger only because we intentionally execute
candidate code inside the hardened one-job sandbox and give that job:

- no repository secrets;
- no controller/JIT-registration credentials;
- `permissions: contents: read` only;
- no write-capable GitHub token;
- `persist-credentials: false` after checkout;
- only same-private-repository PRs;
- trusted owner/actor gate;
- exact comment SHA == current PR-head SHA;
- allow-listed execution profile.

Longer-term, eliminating even the read-only `GITHUB_TOKEN` from candidate code
can be researched by moving source checkout into a trusted pre-job materializer,
but this is not required for the first pilot.

References:

- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target
- https://docs.github.com/en/actions/concepts/security/compromised-runners
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

### 5. systemd + cgroup v2 is a strong native pilot boundary on this host

Ubuntu/systemd supports the controls the design needs:

- `NoNewPrivileges=`;
- `ProtectSystem=strict`;
- `ProtectHome=yes`;
- `ProtectProc=invisible`;
- `CapabilityBoundingSet=`;
- `DevicePolicy=closed/strict` + `DeviceAllow=`;
- `IPAddressAllow=/IPAddressDeny=`;
- `RestrictAddressFamilies=`;
- `MemoryHigh=/MemoryMax=`;
- `CPUQuota=`;
- `TasksMax=`;
- systemd/cgroup kill semantics.

The Lambda probe reports Ubuntu 22.04.5, systemd 249, kernel 6.8 and unified
cgroup v2, so the documented Jammy-era resource controls align well with the
actual host.

**Decision:** native systemd sandboxing remains the first pilot isolation layer.
Do not add Kubernetes, Docker-in-Docker or a VM layer merely to emulate cloud CI.

References:

- https://manpages.ubuntu.com/manpages/jammy/man5/systemd.exec.5.html
- https://manpages.ubuntu.com/manpages/jammy/man5/systemd.resource-control.5.html

### 6. GPU access must be explicit, not inherited

The Lambda probe shows the NVIDIA character devices are currently broadly
read/write accessible. A dedicated UID alone therefore does **not** enforce GPU
assignment.

On cgroup v2, systemd implements `DevicePolicy=` / `DeviceAllow=` with eBPF
device filtering.

**Decision:** GPU profiles must use `DevicePolicy=closed` (or strict if the
runtime survives it) plus explicit NVIDIA control/UVM nodes and only the assigned
GPU device node(s). Verify this empirically before the first model run.

The runner must never rely solely on `CUDA_VISIBLE_DEVICES`; that is a
cooperative visibility mechanism, not a security boundary.

### 7. Network segmentation is mandatory on this host

The Lambda probe observed production PostgreSQL listening on wildcard IPv4/IPv6,
plus Tailscale and multiple local development/service listeners.

GitLab and Buildkite both recommend network segmentation for self-managed build
workers. systemd can enforce cgroup-level IP allow/deny rules.

**Decision:** the pilot must deny runner access to:

- loopback except the local DNS stub required by the host;
- RFC1918/local-campus/private ranges;
- CGNAT/Tailscale ranges;
- link-local addresses;
- IPv6 ULA/link-local/loopback;
- specifically identified production service addresses.

Public Internet egress remains allowed for GitHub/PyPI/Hugging Face.

Because the current resolver is `127.0.0.53`, the policy should allow only that
specific stub address while continuing to deny the rest of `127.0.0.0/8`.

Do not authorize P2 until the actual cgroup-BPF network policy is tested with
positive and negative probes.

### 8. Rootless GPU containers are a credible *second* boundary, not the pilot
prerequisite

NVIDIA now supports Container Device Interface (CDI) and explicitly documents
that CDI improves compatibility with rootless containers; Podman can request
specific NVIDIA CDI devices.

The Lambda probe shows unprivileged user namespaces are enabled, but Podman is
not currently installed.

**Decision:** do not add a container runtime to P1 solely for isolation. First
prove the native project-UID/systemd model. If we later want an additional
filesystem/image boundary or pinned userspace environment, evaluate rootless
Podman + NVIDIA CDI as the preferred second-stage container design.

Never grant the runner the existing Docker socket.

References:

- https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html
- https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

### 9. Persistent caches must not be writable trust carry-over from candidate
jobs

GitHub explicitly warns that caches are not signed/verified and can cause code
execution when poisoned. Buildkite similarly recommends never caching output
from untrusted builds and separating/scoping caches.

Hugging Face's native cache is already revision/blob content-addressed:
immutable snapshots point to hashed blobs.

The first draft allowed a project-private writable persistent cache. That is too
permissive for anything that may later be executed/deserialized.

**Revised decision:**

- workspace: always ephemeral/destructive;
- candidate-job writable cache: ephemeral staging only;
- long-lived executable/model dependency cache: written/promoted only by trusted
  cache-management/default-branch operations;
- jobs consume promoted model/dependency snapshots read-only;
- cache identities include immutable model revision/digest + runtime identity;
- a cache miss is allowed to download into job-local staging but is **not**
  automatically promoted to the long-lived cache;
- never cache credentials or candidate-generated executables as trusted shared
  state.

This is especially important for model formats/code that can execute custom
Python during loading.

References:

- https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching
- https://buildkite.com/docs/pipelines/best-practices/caching
- https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache

### 10. Use a GitHub App for the controller when practical

GitHub recommends GitHub App authentication for runner scale sets. GitHub Apps
can be installed on selected repositories in a personal account.

Repository-scoped ARC/JIT operations require powerful repository administration
permission, making credential containment important.

**Decision:**

- target: private GitHub App installed only on explicitly opted-in repositories;
- controller stores App key/installation metadata outside job-readable paths and
  exchanges for short-lived installation tokens;
- pilot fallback: narrowly scoped fine-grained PAT only if App integration
  blocks bring-up;
- project job never receives either credential.

The Scale Set Client itself recommends GitHub App credentials.

References:

- https://docs.github.com/en/actions/how-tos/manage-runners/use-actions-runner-controller/authenticate-to-the-api
- https://docs.github.com/en/apps/using-github-apps/installing-your-own-github-app
- https://github.com/actions/scaleset

## Host-specific constraints from P0

The read-only Lambda probe materially supports the selected architecture:

- Ubuntu 22.04.5 / kernel 6.8 / systemd 249;
- unified cgroup v2 with CPU, memory, pids and related controllers;
- unprivileged user namespaces enabled;
- 32 logical CPUs and about 270 GB RAM;
- two RTX A4500 GPUs, 20,470 MiB each, linked by NVLink;
- no active GPU compute process at probe time;
- `ci-research-engine` does not yet exist;
- `/home/atrott` is mode 0750, so a separate UID naturally loses traversal
  without group membership;
- Docker socket is root:docker 0660 and the current `atrott` identity is not in
  the docker group;
- production PostgreSQL is listening on wildcard IPv4 and IPv6;
- DNS is provided through the local systemd-resolved stub at 127.0.0.53 with
  campus and Tailscale upstreams;
- about 136 GB of free space was reported on the current root filesystem.

P0 also exposed two follow-up items:

1. the original `findmnt` invocation did not return filesystem metadata, so P1
   must resolve the `/srv` filesystem type/quota capability before promising
   hard disk quotas;
2. PostgreSQL client/server binaries were not generally visible in the probe
   PATH even though `pg_config` exists, so the CPU-test database strategy must
   locate the actual PostgreSQL bindir before assuming native ephemeral clusters.

## Revised recommended topology

```text
GitHub private repository
        │
        │ trusted default-branch /lambda-ci exact-SHA trigger
        ▼
GitHub Actions Runner Scale Set API
        │
        ▼
ci-controller                    (unprivileged)
  official pinned actions/scaleset listener
  repo-scoped GitHub App credential
  no project/home/production/root authority
        │
        │ structured provision request only
        ▼
workspace-ci-provisioner         (root, local-only)
  NO GitHub credential
  root-owned project/profile manifest
  validates paths/resources/devices/network policy
        │
        ▼
systemd transient sandbox
User=ci-research-engine
  one-job JIT runner
  fresh runner config + worktree
  read-only promoted caches
  ephemeral writable staging
  no sudo / no Docker socket / no personal home
  explicit network deny policy
  explicit GPU device policy
        │
        ▼
GitHub logs/check/artifacts
        │
        ▼
runner auto-removal + cgroup kill + leak checks + work/config deletion
```

## Scale-set policy

Initial:

- one repository-scoped scale set: `lambda-research-engine`;
- max concurrency: 1;
- min idle runners: 0 during security bring-up;
- each runner one job only.

After closed-loop stability:

- consider `minRunners=1` while a project is actively being developed if cold
  runner provisioning becomes meaningful;
- keep max concurrency 1 until global GPU/resource arbitration is separately
  validated;
- additional repositories get separate scale sets **and** separate project UIDs.

## What the research rejected

- one long-lived runner under `atrott`;
- one unrestricted runner shared across all projects;
- Docker socket / Docker group access;
- privileged Docker-in-Docker;
- persistent mutable checkout reuse;
- candidate-controlled Lambda workflow YAML;
- secrets/write-capable GitHub tokens inside candidate jobs;
- candidate-written long-lived model/dependency caches;
- Kubernetes/ARC merely to obtain ephemeral semantics on one workstation;
- VMs/microVMs as the initial GPU pilot;
- allowing production-service access just because the Lambda is the production
  host.

## What remains to prove before host mutation

The external research is sufficient to choose the architecture, but P1 should
not yet install/register the runner.

The next static implementation needs:

1. pinned `actions/scaleset` client identity and build/update strategy;
2. unprivileged `ci-controller` design;
3. narrow root provisioner protocol and root-owned manifest;
4. exact systemd unit/profile definitions;
5. read-only/trusted cache-manager layout;
6. network policy with positive/negative tests;
7. device-policy probe for exactly one A4500;
8. corrected filesystem/quota probe;
9. PostgreSQL bindir/test-database strategy;
10. kill switch.

Only then should P2 create users/services and register the first one-job runner.
