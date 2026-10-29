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
