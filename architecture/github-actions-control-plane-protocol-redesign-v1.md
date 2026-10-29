# GitHub Actions Control-Plane Protocol Redesign v1 — Initial Research

## Problem statement
The current control plane mixes three concerns in one path:

1. **GitHub scheduling/lifecycle** — queue assignment, scale-set messages, JIT registration, runner lifecycle.
2. **Workspace authority/policy** — repository, actor, PR head, workflow identity, workload class, resource/security contract.
3. **Human command encoding** — slash-command text embedded into the GitHub job display name.

The third concern has leaked into the first two. A human-readable job name is currently used as a serialized protocol:
`wc-admission-v1|workload=...|pr=...|request=<free-form comment body>`.

That string is independently interpreted by multiple layers. A request can therefore be valid according to one parser and invalid according to a downstream parser even though no authority-relevant fact changed.

## Initial end-to-end graph

```text
PR issue comment
    |
    v
trusted default-branch workflow
  - filters actor/association
  - copies entire comment body into job display name
    |
    v
GitHub Actions service / runner scale set
  - routes by runs-on / scale-set
  - emits typed JobAvailable/Assigned/Started/Completed messages
    |
    v
unprivileged workspace-ci controller
  - consumes Runner Scale Set Client messages
  - parses job display name
  - calls GitHub REST to attest run/job/workflow/PR
  - generates JIT config and deterministic local request identity
    |
    v
root provisioner Unix socket
  - schema-v2 request
  - resolves project manifest / route / execution contract
  - reparses attestation.job_display_name
  - mints + consumes admission
  - builds launch spec
    |
    v
runtime dispatcher
  - maps execution profile to systemd/JIT runner launch
    |
    v
ephemeral GitHub runner
  - workflow reparses original comment body again for candidate SHA/options
  - validates candidate
  - executes payload
    |
    v
JobStarted / JobCompleted + durable request/cleanup state
```

## Architectural finding
The system already uses GitHub's **Runner Scale Set Client**, which is the correct upstream primitive for a non-Kubernetes custom autoscaler. GitHub explicitly describes the Scale Set Client as the standalone Go client for custom autoscaling on VMs, containers, on-prem infrastructure, and cloud services, while ARC is the production reference implementation for Kubernetes.

Therefore we are **not** reinventing GitHub's scheduler itself. We are, however, reinventing a policy/admission/scheduling layer on top of it, and the current design accidentally treats a display string as an instruction stream.

## External architecture comparison

### GitHub ARC / Runner Scale Set Client
- GitHub owns job matching and scale-set assignment.
- The client exposes typed lifecycle messages and current scale-set statistics.
- Scaling should use `TotalAssignedJobs`, not inferred counts of individual lifecycle messages.
- Messages are acknowledged after handling and can be redelivered.
- Ephemeral/JIT runners are the intended lifecycle.

**Lesson:** preserve GitHub's scheduler semantics. Our controller should be a capacity/provider adapter plus policy-attestation boundary, not a second scheduler.

### GitLab Runner taskscaler/fleeting
GitLab separates:
- runner/job polling,
- taskscaler bookkeeping/autoscaling,
- infrastructure-provider abstraction (fleeting),
- executor implementation.

**Lesson:** separate queue/lifecycle logic from compute-provider logic and from policy.

### Buildkite stacks/queues
Buildkite defines a stack as a controller that receives scheduled jobs and turns them into running agents. It issues job-acquisition tokens to ephemeral agents rather than giving workers the controller's long-lived authority.

**Lesson:** reserve jobs and hand workers narrowly scoped execution authority; do not overload routing labels/display strings with policy semantics.

## Proposed direction

### 1. Job display names become non-authoritative
Use them only for observability/correlation. No root policy decision may depend on parsing a free-form job name.

### 2. One canonical typed request envelope
Define something like `WorkspaceCIRequestV1` with explicit fields:
- protocol_version
- request_id
- repository_id
- workflow_run_id
- workflow_job_id
- workflow_path
- workflow_blob_sha
- event_type
- actor
- pull_request_number
- candidate_sha
- operation
- workload_class
- resource_contract_id
- option object / typed parameters
- lifecycle attempt / reassignment identity
- evidence timestamps/digests

No field changes meaning between layers.

### 3. Parse human intent exactly once
The slash command is an ingress UI, not the protocol. A trusted producer/compiler converts it into the canonical request. Everything downstream consumes structured data.

### 4. Root policy validates typed claims, not producer syntax
Root should validate:
- schema/version,
- exact project/workflow/contract bindings,
- typed operation and parameter ranges,
- replay/digest identity,
- resource/security constraints.

It should not parse the original comment body or reconstruct the controller's grammar.

### 5. Separate rejection from controller liveness
A policy rejection is a terminal request outcome with a durable reason. It must not terminate the listener process. Listener death should be reserved for loss of its own invariant or unrecoverable transport/session failure.

### 6. Executor-facing builders
Executors should call a typed builder/policy surface, not synthesize slash commands by hand. The builder must know the accepted operation schema and produce either a valid request or a local validation error before GitHub is triggered.

### 7. Protocol compatibility tests
For every request variant:
`producer -> canonical envelope -> controller attestation -> root admission -> launch-spec simulation`
must be tested as one pipeline.

Property/state-machine tests should cover:
- valid operation variants,
- malformed fields,
- duplicated/redelivered messages,
- JobAvailable -> JobAssigned -> Started -> Completed,
- cancellation/reassignment,
- controller restart,
- provisioner restart,
- stale aggregate statistics,
- rejected policy,
- cleanup failure,
- start-limit recovery.

## Major design question to resolve
The current issue-comment trigger does not expose the PR candidate SHA as the workflow's own `GITHUB_SHA`; issue-comment workflows run from the default branch. We need a clean ingress representation for PR number, candidate SHA, and operation parameters that does not turn `jobDisplayName` into the protocol. Candidate options include:
- a durable structured request object keyed by an opaque request/comment ID;
- a dedicated GitHub App/webhook ingress that compiles issue-comment events into typed requests;
- a small trusted dispatcher workflow that records a canonical request artifact/state before scheduling;
- route-per-operation only where operations are truly distinct security/resource classes.

This must be decided from actual GitHub API capabilities, not assumed.

## Live-system rule
Do not apply the current optional-qualifier parser hotfix to Lambda as the final architecture. It may remain useful as incident evidence, but live promotion is paused until the protocol redesign has a migration story.


## System inventory: semantic ownership defects

The first repository inventory found that the same logical request currently crosses at least these interpretation boundaries:

| Layer | Current input | Current interpretation | Architectural status |
|---|---|---|---|
| issue-comment workflow | `github.event.comment.body` | prefix check + later shell token extraction | legitimate ingress parsing |
| workflow job name | entire comment body | serialized into `wc-admission-v1|...|request=<body>` | **wrong abstraction: display field becomes wire protocol** |
| controller workload router | `JobDisplayName` | extracts `workload=` and request grammar | duplicate interpretation |
| controller attestor | `JobDisplayName` + REST | reparses PR/command/SHA/optional qualifier | duplicate interpretation |
| root generic admission | `attestation.job_display_name` | independently reparses route command/SHA | duplicate interpretation across language boundary |
| workflow first step | original comment body | reparses candidate SHA/options | duplicate interpretation, but appropriately inside trusted workflow |
| execution-contract resolver | workload/route strings | maps to profile/resources/model/runtime | legitimate typed policy if the route identity itself is canonical |

The controller and root are therefore not merely validating the same typed fact. They are each implementing their own compiler from a human string into authority semantics.

A second independent defect is liveness coupling: `sendProvisionRequest` converts root `REJECTED` into a Go error; the scaler returns that error to the official listener; `listener.Run` exits; systemd restarts the whole controller. A normal policy outcome is therefore represented as controller-process failure.

## Scheduler boundary

The official Scale Set Client already provides:
- typed `JobAvailable`, `JobAssigned`, `JobStarted`, and `JobCompleted` messages;
- stable GitHub identities including workflow run/job, repository/owner, workflow ref, event name, labels, and timestamps;
- current scale-set statistics, including `TotalAssignedJobs`;
- redelivery/acknowledgement semantics.

This means the local design should not reconstruct a second queue scheduler. Its responsibilities are narrower:

```text
GitHub Actions scheduler
  owns: queue, matching, assignment, lifecycle, reassignment
             |
             v
Scale Set Client / listener
  owns: session, polling, ack, current scheduler statistics
             |
             v
Workspace policy adapter
  owns: trusted workflow identity -> local execution contract
             |
             v
Capacity provider
  owns: JIT runner + systemd sandbox + resource realization
```

## Recommended protocol architecture

### Invariant P0 — human commands are ingress syntax only
Slash-command text is parsed by the trusted default-branch workflow/dispatcher. It is never a root-policy wire format.

### Invariant P1 — infrastructure admission is keyed by GitHub identity, not display text
The infrastructure request identity should be derived from canonical GitHub fields such as:
- repository owner/name;
- scale-set ID/name;
- workflow run ID;
- canonical workflow job ID;
- trusted workflow path/ref/blob;
- event type;
- lifecycle attempt / assignment identity.

`JobDisplayName` may be logged for humans but is not an authority input.

### Invariant P2 — trusted workflow identity selects the local execution contract
Root-owned policy maps a verified workflow identity to:
- project;
- lane/scale set;
- execution contract;
- resource profile;
- optional exact model/runtime bindings;
- filesystem/network/secrets/state-effect classes.

The mapping key is a structured tuple, not a string embedded in the job name.

### Invariant P3 — candidate SHA is workflow payload, not scheduler authority
For `issue_comment`, GitHub documents that the workflow executes from the default branch, not the PR head. The trusted workflow already has the event payload and read-only `GITHUB_TOKEN`; it can validate the requested candidate SHA against the PR head before checkout.

Therefore the root provisioner generally does **not** need to understand the candidate SHA in order to decide whether it may create the sandbox. It needs to know that the scheduled job came from an exact trusted workflow whose sandbox contract is safe for untrusted candidate execution.

This removes the strongest reason the candidate SHA was smuggled through `JobDisplayName`.

### Invariant P4 — resource/security variants are routes, not free-form options
If two operations require different root authority, GPU count, model/runtime mounts, network class, or secrets, they are different policy routes/contracts. Use:
- distinct trusted workflow identity, or
- another typed static route identifier that is generated from root-owned policy.

Do not dynamically widen root authority because a comment contains an extra word.

Options that do **not** alter the security/resource envelope remain workflow-level typed parameters and do not participate in runner provisioning.

### Invariant P5 — one canonical envelope
The controller sends a versioned structured envelope, tentatively:

```json
{
  "schema_version": 3,
  "request_id": "<uuid/deterministic job-attempt id>",
  "github": {
    "repository": "owner/repo",
    "scale_set_id": 1,
    "scale_set_name": "lambda-workspace-control",
    "workflow_run_id": 123,
    "workflow_job_id": 456,
    "workflow_path": ".github/workflows/...",
    "workflow_ref": "...@refs/heads/main",
    "workflow_blob_sha": "<git blob>",
    "event_name": "issue_comment",
    "actor_login": "..."
  },
  "route": {
    "route_id": "control-validation",
    "execution_contract_id": "control-small-ci-v1"
  },
  "runner": {
    "runner_name": "...",
    "jit_config": "<opaque secret>"
  }
}
```

The root may verify schema, identity bindings, policy membership, replay digest, and resource invariants. It must not reinterpret the original human command.

### Invariant P6 — rejection is data, not process failure
Provisioner responses are an algebraic result type:

```text
ACCEPTED | DUPLICATE | BUSY | POLICY_DENIED | TERMINAL_FAILURE
```

`POLICY_DENIED` is a terminal request result that removes/marks the local pending job and leaves the listener alive. Only controller invariant corruption, session failure, or unrecoverable transport corruption may terminate the controller process.

### Invariant P7 — lifecycle and policy state machines are separate
Scheduler state:
`AVAILABLE -> ASSIGNED -> STARTED -> COMPLETED/CANCELED/REASSIGNED`

Local execution state:
`OBSERVED -> ATTESTED -> ADMITTED -> JIT_CREATED -> LAUNCHED -> CLEANED`

Policy result:
`ALLOW | DENY(reason)`

These states may reference one another, but none is encoded by overloading another state machine's string values.

## Two implementation candidates

### Candidate A — workflow identity -> contract mapping (recommended)
Keep the official Scale Set Client and current systemd capacity provider. Remove workload/command/SHA parsing from job names. Controller attests exact workflow identity via REST; root maps workflow identity to a root-owned execution contract.

Benefits:
- minimal change to proven GitHub scale-set/JIT machinery;
- keeps root free of GitHub credentials;
- removes cross-language grammar duplication;
- supports many research workflows without one scale set per workflow;
- preserves exact model/runtime binding in root manifests where needed.

### Candidate B — scale set == execution contract
Create a separate scale set for each materially distinct resource/security contract and make the controller/provisioner almost completely job-agnostic.

Benefits:
- strongest alignment with scheduler queue semantics;
- almost no per-job policy parsing.

Costs:
- more scale sets/controllers;
- poor fit where many workflow/model routes share one hardware envelope but require different exact root-owned mounts.

Current recommendation: **Candidate A**, with scale sets representing broad isolation/resource lanes and trusted workflow identity selecting the narrower execution contract.

## Executor-policy redesign

Executors should not hand-author infrastructure protocol strings.

The executor-facing API should expose a generated catalog such as:

```text
workspace_control.validate(pr, sha, mode=STANDARD)
workspace_control.host_attest(pr, sha)
research_engine.cpu_validate(pr, sha)
research_engine.run_experiment(pr, sha, experiment_id=<enum>)
```

The builder validates parameters locally from the same versioned route catalog that generates workflow/policy tests. It may emit a slash command because GitHub comments are the user interface, but the emitted text is no longer consumed by the infrastructure admission pipeline.

A valid executor request can therefore fail later only for a changed external fact (PR closed/head moved, workflow policy revoked, capacity unavailable), never because two parsers disagree on its grammar.

## Verification strategy

The repository-only gate before any live migration should include:

1. **Protocol compiler tests** — every route catalog entry generates a valid typed envelope.
2. **Cross-layer compatibility tests** — all admitted route/workflow identities survive controller -> root -> launch-spec simulation.
3. **Property tests** — arbitrary valid parameter combinations cannot create parser divergence.
4. **State-machine model tests** — duplicate/redelivered/assigned/canceled/reassigned messages and controller/provisioner restarts.
5. **Fault injection** — root DENY, BUSY, socket timeout, JIT generation failure, cleanup failure; listener liveness must be preserved where the failure is request-local.
6. **Migration equivalence tests** — existing research-engine and workspace-control trusted workflows resolve to the same or narrower execution contracts before live cutover.


# Whole-system controller model

## Controller census

The current architecture contains more than "the Git controller."

### Runner scale-set controllers
There are five registry-managed instances of the same pinned Go controller:

| Project | Current lane | Current scale set | Registered routes |
|---|---|---|---:|
| workspace-control | cpu | `lambda-workspace-control` | 1 |
| PADataset | cpu | `lambda-padataset` | 1 |
| PADataset | gpu | `lambda-padataset-gpu` | 1 |
| research-engine | cpu | `lambda-research-engine` | 1 |
| research-engine | gpu | `lambda-research-engine-gpu` | 19 |

All five currently execute as the same local Unix identity `ci-controller` and share the same root provisioner service.

### Other GitHub-facing control processes
Two additional controllers are operationally distinct and should remain separate authority planes:

1. **Maintenance controller** — polls a dedicated workspace-control issue, parses `/workspace-ci-maintain` once, builds a typed JSON request, and submits it to a separate root maintenance service.
2. **Project reconciliation controller** — observes successful trusted main-branch reconciliation workflow runs, fetches exact registry/manifests/blobs, builds a typed JSON request, and submits it to the root reconciler.

These are useful internal reference architectures because neither asks root to reparse a human command.

### Legacy controller generation
The repository still retains non-templated `workspace-ci-controller.service` and `workspace-ci-controller-gpu.service`, plus legacy Research Engine P2B/P3/P4 self-hosted workflows. The redesign must explicitly retire or quarantine these artifacts so they cannot create a second scheduler generation accidentally.

## Registered workflow census

The root registry currently admits exactly 23 trusted routes:
- workspace-control: 1;
- PADataset: 2;
- research-engine: 20.

Every registered route's pinned trusted workflow blob currently exactly equals the file on that repository's current `main`. Therefore the observed false-rejection incidents are not caused by trusted-workflow pin drift.

PADataset is fully affected by the current display-string protocol: both CPU and GPU workflows serialize `wc-admission-v1` into the job name and parse the issue comment body.

Research Engine contains three protocol generations simultaneously:
- legacy self-hosted label workflows (P2B/P3/P4);
- current generic `wc-admission-v1` workflows;
- ordinary GitHub-hosted workflows unrelated to the Lambda scale-set controller.

# Runner-class model

## Scale-set homogeneity is a hard invariant

GitHub defines a runner scale set as a group of homogeneous runners. The pinned official Scale Set Client reference implementation acquires jobs, scales from `TotalAssignedJobs`, and starts one homogeneous runner implementation; it does not inspect a job-specific DSL to select hardware or mounts.

Define a runner-class equivalence relation:

Two routes are in the same runner class iff a runner provisioned before knowing which of those routes GitHub will assign is both:
1. **safe** for either route; and
2. **sufficient** for either route.

At minimum the equivalence key includes:
- project isolation identity;
- execution contract;
- systemd/resource class and ceilings;
- GPU cardinality/device authority;
- payload network class;
- filesystem/cache class;
- state-effect class;
- exact model binding;
- exact runtime binding;
- any future secret/trusted-object binding that alters the root launch envelope.

Route names, experiment names, and candidate SHA are explicitly excluded unless they change one of the above capabilities.

## Current partition

Four current scale sets are already homogeneous:
- Workspace Control CPU;
- PADataset CPU;
- PADataset GPU;
- Research Engine CPU.

`lambda-research-engine-gpu` is not homogeneous. It contains jobs requiring:
- zero GPUs;
- one GPU;
- two GPUs;
- public payload network;
- offline payload network;
- no model/runtime mount;
- exact runtime-only mount;
- exact model+runtime mount.

One route named `cpu-validation-exact-provenance` is even placed on the current GPU lane while its accepted contract is CPU-only.

## Proposed nine runner classes

| Runner class | Project | Profile | GPU | Exact bindings | Routes |
|---|---|---|---:|---|---|
| `workspace-control-control-small-v1` | workspace-control | control-small | 0 | none | control-validation |
| `padataset-cpu-public-v1` | PADataset | cpu-test | 0 | none | cpu-ci |
| `padataset-gpu-single-public-v1` | PADataset | gpu-small | 1 | none | gpu-ci |
| `research-cpu-public-v1` | research-engine | cpu-test | 0 | none | cpu-test; cpu-validation-exact-provenance |
| `research-gpu-single-public-v1` | research-engine | gpu-small | 1 | none | gpu-experiment-public |
| `research-gpu-single-runtime-v1` | research-engine | gpu-small | 1 | exact Qwen expanded runtime, no model | gpu-small; reranker; oracle-query; AMR graph |
| `research-model-single-offline-v1` | research-engine | gpu-small | 1 | exact Qwen model+runtime | model-eval-single-gpu |
| `research-model-dual-offline-v1` | research-engine | gpu-heavy | 2 | exact Qwen model+runtime | model-eval-dual-gpu |
| `research-model-dual-public-v1` | research-engine | gpu-heavy | 2 | exact Qwen model+runtime | Local EXTRACT dual-GPU/public families |

This is nine project-scoped scale sets total. It is not nine different controller binaries: one generic controller implementation may still be instantiated nine times from a runner-class catalog.

## Manifest redesign

The current manifest schema is lane-centric and the controller hardcodes:
- `cpu -> lambda-<project>`;
- `gpu -> lambda-<project>-gpu`.

That schema cannot represent the actual workload topology without parsing per-job route strings.

Replace project `lanes` with explicit root-owned `runner_classes`:

```json
{
  "runner_classes": {
    "research-model-dual-public-v1": {
      "scale_set_name": "lambda-research-engine-model-dual-public",
      "runner_prefix": "lambda-research-engine-model-dual-public-",
      "execution_contract_id": "model-dual-public-v1",
      "model_id": "qwen3.5-4b",
      "runtime_id": "qwen35-vllm-cu129-image-native-sampler-v3",
      "max_runners": 1
    }
  },
  "routes": {
    "model-eval-local-extract-wave7a3": {
      "runner_class_id": "research-model-dual-public-v1",
      "trusted_workflow": {
        "path": ".github/workflows/lambda-ci-local-extract-wave7a3.yml",
        "job_name": "local-extract-wave7a3",
        "blob_sha": "..."
      },
      "ingress": {
        "command": "/lambda-ci-local-extract-wave7a3",
        "parameter_schema": "candidate-sha-v1"
      }
    }
  }
}
```

The ingress command is executor/UI metadata. It does not cross into the root launch request.

# Trust-boundary model

## GitHub scheduler -> controller
Authenticated input is the Scale Set Client message and REST observations, not the human string.

The pinned message type already supplies:
- repository owner/name;
- workflow run ID;
- workflow ref;
- event name;
- request labels;
- runner request ID;
- lifecycle timestamps;
- job ID when available.

The controller verifies the exact trusted workflow identity and GitHub lifecycle facts.

## Controller -> root provisioner
The root launch request should be keyed by `runner_class_id`, not `workload_class`.

The root launch envelope is already known before any candidate payload executes because the runner class is homogeneous.

A v3 request therefore needs only infrastructure authority such as:

```json
{
  "schema_version": 3,
  "request_id": "...",
  "runner_class_id": "research-model-dual-public-v1",
  "runner_name": "...",
  "jit_config": "...",
  "github_execution": {
    "repository": "adamtrott78/research-engine",
    "workflow_run_id": 123,
    "run_attempt": 1,
    "workflow_path": ".github/workflows/lambda-ci-local-extract-wave7a3.yml",
    "workflow_blob_sha": "...",
    "event_name": "issue_comment",
    "actor_login": "adamtrott78"
  }
}
```

The original comment body, candidate SHA, PR number, experiment options, and display-name serialization are absent from the root protocol unless a future root capability genuinely requires them.

## Local controller identity must be bound to runner class

Today all scale-set controllers run as `ci-controller`, while root authorizes the shared Unix peer UID. Therefore root cannot distinguish which controller instance sent a request.

A v3 design must not rely solely on a request-provided `runner_class_id`. Options, in descending isolation strength:

1. distinct unprivileged controller UID per runner class, mapped by root `SO_PEERCRED` to one allowed class;
2. class-specific authenticated local socket/credential with a process sandbox that prevents one controller instance acquiring another class credential;
3. distinct project controller identity plus a second unforgeable class binding.

The selected mechanism must make this invariant true:

> A compromised controller instance cannot cause root to launch a runner class stronger than the class that controller is locally authorized to manage.

The existing shared-UID design does not prove that invariant.

# Job-correlation model

## Why correlation remains necessary
`JobAvailable` can omit `JobID`. The current implementation resolves the canonical REST job by matching the dynamic job display name.

Removing authority parsing therefore requires a replacement correlation rule.

## Proposed rule
Each trusted route declares one static self-hosted job identity. For a Scale Set Client message, the controller:

1. validates repository, event, workflow run ID, workflow ref and configured scale-set labels;
2. resolves the workflow path from `JobWorkflowRef`;
3. maps that exact trusted workflow to the runner class from root-synchronized policy;
4. reads the workflow run via REST and verifies repository/event/actor/default-branch workflow identity;
5. lists jobs for the run;
6. selects exactly one nonterminal REST job matching the configured static job name and expected runner-class labels;
7. records the REST numeric job ID as the canonical job identity;
8. refuses acquisition if the correlation is zero or ambiguous.

`JobDisplayName` may be retained as an opaque static equality/correlation field. No component parses tokens out of it.

A stronger simplification is available where a trusted workflow contains exactly one self-hosted job: the canonical attempt key can be `repository + workflow_run_id + run_attempt + workflow_path + runner_class_id`, with REST job ID added after observation.

# Error and acknowledgement algebra

The Scale Set Client listener acknowledges a message only when `Scale` returns nil. Any non-nil error terminates the listener and deliberately leaves the message for redelivery.

Therefore every local outcome must be typed before returning from `Scale`.

### Request-local terminal outcomes
Examples:
- workflow not trusted;
- ambiguous job correlation;
- root policy denial;
- duplicate terminal request.

Action:
- persist a bounded denial/terminal receipt;
- remove any unconsumed JIT registration;
- update local pending state;
- return **nil** to the listener so the message is acknowledged.

### Capacity/transient outcomes
Examples:
- root BUSY;
- temporary provisioner socket failure;
- temporary GitHub REST failure.

Action depends on whether safe redelivery is required. The retry policy must be explicit and idempotent, rather than implicitly restarting the whole controller.

### Controller/session-fatal outcomes
Examples:
- corrupt durable controller state;
- invalid scale-set session;
- impossible response schema / trust-boundary corruption.

Only these may return an error that stops `listener.Run`.

# Three separate GitHub control planes

The redesign should not force one protocol everywhere.

### Runner execution plane
Needs Scale Set Client lifecycle + homogeneous runner classes + trusted workflow correlation + root capacity provisioner.

### Maintenance plane
Already has the desired shape:
`GitHub owner command -> one parser -> typed operation -> root maintenance service -> durable receipt`.

Keep it separate. Add generated executor builders and schema tests, but do not route maintenance through the runner scheduler.

### Reconciliation plane
Already has an even cleaner shape:
`trusted successful workflow/run -> exact policy documents/digests -> typed root reconciliation -> durable receipt`.

Keep it separate. It is policy deployment, not job scheduling.

Host attestation belongs to the maintenance/diagnostic plane, not as a free-form qualifier on candidate execution.


# Simplified capacity-provider architecture

The runner-class partition removes the need for job-specific root admission.

## Key observation

A JIT config registers a runner with a scale set, not with one specific workflow job. The official reference scaler:
1. acquires acceptable `JobAvailable` request IDs;
2. reads `TotalAssignedJobs`;
3. starts that many homogeneous runners.

Therefore root provisioning should realize **runner-class capacity**, not compile a workflow request.

## Revised authority split

```text
OWNER / EXECUTOR
  emits human ingress command
        |
        v
TRUSTED DEFAULT-BRANCH WORKFLOW
  command grammar + candidate/experiment parameter checks
        |
        v
GITHUB ACTIONS SCHEDULER
  queue + scale-set routing + lifecycle
        |
        v
RUNNER-CLASS CONTROLLER (unprivileged)
  - authenticated Scale Set Client session
  - exact trusted workflow/event/actor attestation
  - AcquireJobs only for allowed workflow jobs
  - scale from TotalAssignedJobs
        |
        v
ROOT CAPACITY PROVIDER
  - authenticate local controller -> fixed runner class
  - validate JIT envelope / runner name
  - realize fixed systemd/resource/model/runtime envelope
  - no workflow command parser
  - no route parser
  - no candidate SHA parser
        |
        v
EPHEMERAL HOMOGENEOUS RUNNER
  executes trusted workflow gate first
  then executes exact candidate payload
```

## Root request becomes a capacity request

A strong v3 request can be reduced to:

```json
{
  "schema_version": 3,
  "request_id": "<runner-instance request id>",
  "runner_name": "<class prefix + opaque suffix>",
  "jit_config": "<opaque GitHub JIT registration>"
}
```

The root service derives `project_id`, `runner_class_id`, execution contract, resource ceiling, GPU authority, network class, exact model/runtime mounts, and filesystem policy from the authenticated **local controller identity**.

No field supplied by the controller may widen the class.

This is stronger than the current v2 request because a compromised controller cannot claim a different `workload_class` merely by constructing a plausible attestation.

## Local controller authentication

The simplest proof-carrying local identity is a unique unprivileged Unix UID per runner class.

Example:

```text
ci-ctl-wc-control
ci-ctl-pad-cpu
ci-ctl-pad-gpu
ci-ctl-re-cpu
ci-ctl-re-gpu-public
ci-ctl-re-gpu-runtime
ci-ctl-re-model-single
ci-ctl-re-model-dual-offline
ci-ctl-re-model-dual-public
```

Root maps `SO_PEERCRED.uid -> runner_class_id`.

Project-scoped GitHub credentials may be shared read-only among the class-controller UIDs for the same repository, but root launch authority is not shared.

Alternative local proofs (class-specific sockets/credentials or kernel cgroup/service identity) may be evaluated, but the accepted design must provide the same non-forgeability property.

## Controller no longer needs per-job route parsing

For each `JobAvailable`:
- parse no human command;
- inspect GitHub-native fields;
- derive trusted workflow path from `JobWorkflowRef`;
- look up the workflow in the controller's installed allowlist for **this runner class**;
- verify the run via REST: repository, event, actor/triggering actor, workflow path, default-branch run commit;
- verify exact workflow blob at that run commit equals the installed allowlist blob;
- acquire the `RunnerRequestID` only if those checks pass.

The controller does not need candidate SHA, PR number, experiment name, or root route identity to make the acquisition decision.

## Job ID correlation is optional, not foundational

Because root capacity is class-level, the controller does not require a canonical REST job ID before provisioning.

For audit/recovery:
- `WorkflowRunID + run_attempt + trusted workflow path + runner class` forms the stable attempt identity when the trusted workflow has exactly one self-hosted job in that class;
- `JobStarted/JobCompleted` provide the GitHub JobID and runner name later;
- REST job lookup may enrich evidence or resolve recovery, but dynamic display-name parsing is not a prerequisite for safe scaling.

If a trusted workflow ever has multiple jobs targeting the same runner class, each must have a static catalogued job key/name so correlation is deterministic.

# Executor command model

The registered command census shows:
- 22 of 23 current routes consume only `<command> <candidate_sha>`;
- one route, `gpu-experiment-public`, consumes `<command> <candidate_sha> <candidate-id>`.

The third token selects one of two workflow-level resource-probe payloads while the root execution envelope remains the same fixed single-GPU public class.

Therefore there is currently **no legitimate registered use case where a free-form optional command token must change root runner provisioning**.

The executor API can be generated from route schemas:

```text
workspace_control.validate(pr, candidate_sha)
padataset.cpu_validate(pr, candidate_sha)
padataset.gpu_validate(pr, candidate_sha)
research_engine.local_extract_wave7a3(pr, candidate_sha)
research_engine.reasoner_probe(
    pr,
    candidate_sha,
    candidate = QWEN35_9B_Q6 | QWYNTHOS_9B_V2_Q6
)
maintenance.host_attest(project, runner_class)
```

Generated builders may emit GitHub comments as the human interface, but the infrastructure controller never parses those arguments.

# GitHub-level workflow restriction

GitHub runner groups can be configured to allow selected repositories and selected workflows. Where account topology supports it, runner-class groups should use selected-workflow restrictions as an additional scheduler-side allowlist.

This is defense in depth, not a replacement for controller attestation:
- account/organization capabilities may differ;
- root authority must remain correct even if GitHub runner-group policy is misconfigured.


# Local authentication decision

## Selected mechanism: unique controller UID per runner class

Use one unprivileged Unix user for each runner class and preserve one root provisioner socket.

Root authorization becomes:

```text
SO_PEERCRED.uid
      |
      v
root-owned uid -> runner_class_id map
      |
      v
root-owned runner-class catalog
      |
      v
fixed launch envelope
```

The capacity request does not contain an authoritative project or class selector.

### Why this is selected
- kernel-enforced and simple to reason about;
- no HMAC/key-distribution protocol to invent;
- no parsing of systemd cgroup names or process metadata;
- distinct UIDs prevent one class controller from signaling/ptracing another by same-UID rules;
- class state directories can be mode 0700 and UID-owned;
- one root Unix socket can remain, because peer UID is sufficient to derive class.

### Credential grouping
Runner-class controller UIDs for one project may share a **repository-scoped GitHub credential group** because that credential authorizes GitHub control-plane observation for the project, not root launch authority.

Example:
- `workspace-ci-github-workspace-control`;
- `workspace-ci-github-padataset`;
- `workspace-ci-github-research-engine`.

Root launch authority is still per UID/class.

A later credential-hardening pass may replace direct GitHub App private-key sharing with a project-scoped token broker. That is orthogonal to the runner-class protocol and must not reintroduce root authority into the GitHub-facing controller.

## Root peer map
The root catalog records the expected controller Unix user. At service startup, root resolves every user to a numeric UID and rejects:
- missing users;
- duplicate UID mappings;
- duplicate runner prefixes;
- duplicate scale-set names;
- a class whose execution contract/bindings do not resolve exactly.

At request time:
1. read `SO_PEERCRED`;
2. map peer UID to exactly one class;
3. validate runner-name prefix for that class;
4. validate request replay/digest;
5. build launch spec solely from that class.

An unknown peer is a fatal authorization/configuration event, not a recoverable policy denial.

# Policy projections

One source catalog generates two non-authoritative projections plus one root projection.

### Root projection
Contains only:
- controller UID/user -> runner class;
- scale-set/runner prefix identity;
- execution contract;
- resource ceiling;
- exact model/runtime bindings;
- concurrency/quarantine policy.

It contains **no command strings and no candidate parameters**.

### Controller projection
One file per runner class:
- repository;
- scale-set identity;
- max runners;
- exact trusted workflow path/blob/job key;
- allowed event;
- allowed actor/triggering actor policy.

It contains **no root resource-selection grammar** because the controller cannot select a different class.

### Executor projection
Contains:
- human action name;
- target PR requirements;
- slash-command string;
- typed argument schema/enums.

It contains **no root launch semantics**.

The projections share stable IDs but have intentionally different authority surfaces.

# Retry / acknowledgement decision

The pinned Scale Set Client acknowledges a message only after `Scale` returns nil.

The target controller uses this rule deliberately.

### Stable deny
Examples: workflow path not allowlisted, wrong event, wrong actor, wrong exact workflow blob.

- do not acquire the job;
- record bounded denial evidence;
- return nil;
- keep listener alive.

The job remains unacquired; scheduler/account policy or workflow cancellation owns its eventual terminal state.

### Retryable observation/transport failure
Examples: transient GitHub REST outage, temporary scale-set/JIT API error, temporary root socket outage.

- do not convert the condition into a policy denial;
- return a typed retryable error to a **process-local supervisor**;
- supervisor closes/re-establishes the message session after bounded exponential backoff;
- the unacknowledged GitHub message is redelivered;
- the process remains under one systemd activation and does not consume `StartLimitBurst`.

### Root capacity outcomes
- `ACCEPTED`: track runner-instance request.
- `DUPLICATE`: reconcile durable status.
- `BUSY`: remove unconsumed JIT registration and converge on next statistics update.
- `CLASS_QUARANTINED`: keep controller/session alive but advertise/behave as zero executable capacity until maintenance clears it.
- malformed/root protocol corruption: fatal.

### Static configuration failure
Invalid catalog, unknown local peer, duplicate class identity, impossible runner prefix, corrupt durable ledger:
- fail process startup;
- require operator/reconciliation correction.

Systemd restart is reserved for actual process faults, not job-level control flow.
