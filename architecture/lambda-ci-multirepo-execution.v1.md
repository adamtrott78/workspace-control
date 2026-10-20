# Lambda CI Multi-Repository Research Execution v1

Status: **Run-1 architecture freeze; contract only; not installed.**

Owning task: `workspace-lambda-multirepo-research-execution-v1`.

This design generalizes the accepted research-engine GitHub-to-Lambda substrate into a reusable research-compute control plane for explicitly authorized repositories. It does **not** authorize live host changes, PADataset execution, new GPU authority, or production/scientific-state access.

## 1. Accepted baseline and reason for this redesign

The research-engine pilot proved one-job JIT execution, exact workflow/candidate attestation, root/unprivileged separation, bounded CPU/GPU profiles, promoted model/runtime verification, durable terminal receipts, workspace teardown, CPU/GPU residue checks, and lane quarantine semantics.

The remaining problem is structural: repository identity, runner namespace, project UID/root, workload names, and several GPU/model authorization decisions are still embedded in controller/provisioner/runtime source. That makes a new project or experiment look like an infrastructure patch.

Run 1 freezes the opposite invariant:

> A route name is an audit label, not privilege. Root-owned semantic policy is privilege.

## 2. Non-negotiable invariants

The generic substrate MUST preserve:

- one-job ephemeral JIT runners;
- repository + exact trusted workflow + exact open same-repository PR-head attestation;
- root-owned admission and systemd/resource policy;
- GitHub credentials only in the unprivileged controller plane;
- no candidate root/sudo/Docker/control-plane socket access;
- private/local/production-service denial unless a future separately accepted contract says otherwise;
- distinct project UIDs and mutable roots;
- exact promoted-object verification before/after use;
- cleanup as part of job correctness;
- no automatic replay after ambiguous execution;
- cleanup failure -> lane quarantine.

PADataset is public. Its pilot MUST additionally require an allowed trigger actor and an open **same-repository** PR head. Fork PR execution is forbidden even if GitHub would otherwise queue a workflow.

## 3. Authority objects

### 3.1 Project registry

`architecture/lambda-ci-project-registry.v1.json` is the root-owned allowlist of projects.

It identifies only:

- project ID;
- exact GitHub repository;
- repository visibility;
- project-manifest source path;
- desired activation state;
- enabled controller lanes.

It also defines deterministic naming/path templates. Projects do not supply arbitrary Linux users, filesystem roots, scale-set names, runner prefixes, unit names, or install paths.

For project ID `X`, root derives:

- user/group: `ci-X`;
- mutable root: `/srv/workspace-ci/X`;
- CPU scale set: `lambda-X`;
- GPU scale set: `lambda-X-gpu`;
- runner prefixes: `lambda-X-` and `lambda-X-gpu-`;
- transient unit: `workspace-ci-X-<request-id>.service`.

A manifest whose readable derived identity disagrees with these formulas fails closed.

### 3.2 Project manifest v2

A project manifest binds repository-local routes to global execution contracts.

A route owns:

- route/workload ID;
- CPU or GPU lane;
- execution-contract ID;
- trusted default-branch workflow path and exact blob once activated;
- issue-comment command;
- allowed trigger actors;
- exact model/runtime bindings when required.

A route may be experiment-specific for auditability. Adding a route that reuses an accepted execution contract is a **data/config change**, not controller/provisioner/runtime source work.

### 3.3 Execution contracts

`architecture/lambda-ci-execution-contracts.v1.json` contains reusable semantic envelopes.

The privileged runtime dispatch key is the **resolved execution contract**, never the route/workload string.

The root-issued execution spec carries at least:

- execution plane/profile;
- resource class and exact GPU authority;
- network class;
- secret class;
- filesystem class;
- cache class;
- state-effect class;
- model-binding mode;
- runtime-binding mode;
- exact route-bound object identities, if any.

Unknown route or unknown contract fails closed.

## 4. Generic controller model

There remains one controller binary, but root reconciliation creates one configured instance per project/lane.

Controller configuration is required; there are no research-engine defaults. Each instance receives:

- repository URL;
- project ID;
- lane;
- scale-set name;
- runner prefix;
- provisioner socket;
- GitHub App installation identity.

The controller does **not** decide whether a route may use CPU, one GPU, two GPUs, a model, public egress, or a trusted cache. It:

1. receives a scale-set job;
2. parses the strict existing display grammar generically;
3. verifies repository/event/workflow run/job/open same-repo PR head/candidate SHA through GitHub REST;
4. emits attestation plus claimed route and request command;
5. derives deterministic request/runner identity using configured project/lane prefix;
6. sends the v2 request to root.

The existing `wc-admission-v1|workload=...|pr=...|request=... <sha>` grammar can be retained. The hard-coded `requestCommandForWorkload` and profile workload allowlists are removed. Root compares the claimed command, lane and route against the project manifest.

This preserves current research-engine workflow compatibility during migration.

## 5. Root admission and provisioner selection

The provisioner loads the installed project registry, resolves `project_id`, loads exactly that root-installed project manifest, and then resolves:

`project -> route -> execution contract -> route bindings -> root execution spec`.

The request cannot supply:

- execution profile;
- resource class;
- UID/GID;
- filesystem path;
- device;
- network rule;
- model/runtime path;
- systemd property.

Runner-name validation is derived from project ID + lane, not a global research-engine regex.

The provisioner rejects:

- unknown project;
- repository mismatch;
- unknown route;
- route/lane/scale-set mismatch;
- workflow/command/actor mismatch;
- unbound active workflow;
- disabled execution contract;
- missing/extra exact model/runtime binding;
- policy/registry epoch drift;
- derived identity/path mismatch.

## 6. Privileged runtime semantic authorization

Implementation Run 2 removes experiment-name branches such as:

- `MODEL_EVAL_WORKLOADS`;
- `DUAL_GPU_MODEL_EVAL_WORKLOADS`;
- `workload == model-eval-...` checks.

Instead:

- model verification follows `model_binding_mode`;
- expanded-runtime verification follows `runtime_binding_mode`;
- GPU dispatch follows execution profile + resource class + exact GPU count/UUID set;
- network/filesystem/cache/state effects come only from the resolved contract;
- route ID is recorded in receipts but MUST NOT grant capability.

For example, a future `padataset-rf-benchmark-7` route can reuse `gpu-single-public-ci-v1` without a Python/Go source edit.

A new **combination of capability dimensions** still requires a reviewed root policy/contract change. That is intentional.

## 7. Project isolation

Each project has a distinct system UID/GID and writable root.

A candidate runner can see:

- its job workspace;
- its project-local ephemeral home/staging as authorized;
- only exact trusted objects mounted read-only for its route.

It cannot see:

- sibling project mutable roots;
- provisioner/controller/reconciler state;
- controller credentials/JIT material;
- personal home;
- Docker socket;
- production service credentials/state.

Cross-project trusted-object reuse is future-compatible but fail-closed: the global content-addressed store is invisible by default. Root may expose only an explicitly authorized object read-only into a project job namespace. The initial PADataset pilot requires no shared model object.

## 8. Git-driven root reconciliation

Routine approved-project onboarding must not require operator SSH/sudo after the generic substrate's one-time migration.

Run 2/3 therefore introduce a dedicated trusted reconciliation plane:

- source repository: `adamtrott78/workspace-control`;
- trusted default-branch workflow: `.github/workflows/lambda-ci-project-reconcile.yml`;
- allowed actor(s): root registry;
- dedicated unprivileged reconciliation controller identity;
- dedicated root reconciliation socket/group inaccessible to project runners;
- request schema: `lambda-ci-reconciliation-request.v1`.

The workflow may submit only the registry + referenced project-manifest JSON documents and their digests. Root canonicalizes/re-hashes, validates schemas, validates all derivations and the installed authority ceiling, then synthesizes system state using root-owned templates.

The reconciler may create/update:

- project system user/group under deterministic naming;
- project root directories with fixed ownership/modes;
- root-installed registry/project config;
- controller instance config;
- templated systemd controller instances;
- scale-set configuration required by the generic controller.

It may NOT accept arbitrary shell commands, paths, systemd properties, unit bodies, environment variables, credentials, network rules, or device nodes from Git.

V1 reconciliation is add/update only. Project deletion or destructive identity migration remains an explicit operator operation.

Every reconciliation emits a durable receipt binding source workspace-control commit/workflow blob, registry/manifests digests, before/after installed digests, actions taken, and service health.

## 9. GitHub execution topology

Repository-scoped scale sets remain the v1 multi-project mechanism. A selected-repository GitHub App installation can cover research-engine, PADataset and later explicitly approved repositories.

A thin trusted launcher remains in each target repository for the first multi-project acceptance because current attestation semantics are already proven for repo-local workflows.

GitHub supports reusable workflows across repositories and called workflows owned by the same user can use self-hosted runners from the caller's context. That is a later deduplication option, not a Run-1 dependency. We will not switch launcher topology until a dedicated attestation probe confirms the exact `job_workflow_ref`/blob behavior seen by the scale-set controller.

## 10. Public-repository boundary

PADataset is public, so generic onboarding does not mean generic PR execution.

The root project route must require:

- event = `issue_comment`;
- actor in explicit root-owned allowlist;
- open PR;
- PR head repository exactly `adamtrott78/PADataset`;
- candidate SHA exactly the current PR head;
- exact trusted default-branch workflow blob.

Fork heads fail before JIT provisioning.

## 11. Research-engine migration map

Run 2 must replace these source assumptions:

| Current assumption | Generic destination |
| --- | --- |
| controller default repo/project/scale sets | required per-instance controller config generated from registry |
| controller CPU/GPU workload allowlist | generic strict route parser; root route/contract validation |
| controller command switch | command parsed from trusted display claim; root route command comparison |
| controller hard-coded runner prefixes | configured/derived project-lane prefix |
| provisioner default research-engine manifest | root project-registry resolver |
| provisioner research-engine runner regex | derived project-lane prefix validation |
| provisioner service exact gpu-heavy workload set | semantic resolved contract/resource validation |
| runtime model-eval workload sets | model/runtime binding modes in resolved contract |
| runtime dual-GPU workload set | exact profile/resource/GPU authority in resolved contract |
| bootstrap creates only ci-research-engine | root reconciler deterministic project identity creation |
| bootstrap installs only research-engine configs | one-time generic substrate install + subsequent Git reconciliation |

Research-engine remains the regression oracle. Migration MUST preserve the existing route workflow blobs, commands, Qwen identities, GPU UUIDs, cleanup semantics and generic raw `gpu-heavy` denial.

## 12. PADataset P6 pilot

PADataset project ID: `padataset`.

Derived identities:

- user/group: `ci-padataset`;
- root: `/srv/workspace-ci/padataset`;
- CPU scale set: `lambda-padataset`;
- GPU scale set: `lambda-padataset-gpu`.

Initial routes are intentionally small:

- `cpu-ci` -> `cpu-public-ci-v1`;
- `gpu-ci` -> `gpu-single-public-ci-v1`.

Their workflow blob fields remain null until the pilot launcher workflows are created and merged. A null blob can never activate a route.

The first PADataset jobs are non-scientific canaries only. They must not change datasets, results, experiments or paper claims.

## 13. Third-project proof

The schemas deliberately contain no enum of project IDs or repository names beyond the root registry owner ceiling.

Acceptance requires a synthetic third-project fixture to prove that a new project with existing CPU/GPU contracts can be represented with:

- one registry entry;
- one project manifest;
- thin launcher binding(s);

and **zero controller/provisioner/runtime source changes**.

## 14. Run boundaries

### Run 1 — this run

Produce/freeze:

- this architecture;
- project registry + schema;
- execution contracts + schema;
- research-engine migration manifest v2;
- PADataset pilot manifest;
- reconciliation protocol/request schema;
- static contract tests;
- durable task checkpoint.

No live host or target-repo behavior changes.

### Run 2

Implement generic controller, provisioner, runtime and reconciliation code under tests. No live install until full regression/adversarial validation passes.

### Run 3

One bounded root migration/install of the generic substrate. Prove existing research-engine routes still work.

### Run 4

Onboard PADataset via registry/manifest/workflow changes only; run CPU/GPU canaries and mutual-isolation tests.

## 15. Architecture-freeze acceptance

Run 1 is complete only if all are true:

1. experiment-specific route names are non-authoritative in the privileged runtime;
2. project identity/path/scale-set/runner naming is derivable from project ID;
3. target repos cannot invoke reconciliation;
4. PADataset can be represented without generic source changes;
5. a synthetic third project can be represented without generic source changes;
6. public PADataset fork PRs are explicitly denied;
7. existing research-engine route identity can migrate without weakening current gates;
8. no live Lambda or PADataset execution change occurred in Run 1.
