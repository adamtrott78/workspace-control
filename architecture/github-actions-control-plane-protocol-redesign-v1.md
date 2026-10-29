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
