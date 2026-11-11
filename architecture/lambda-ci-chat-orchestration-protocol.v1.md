# Lambda CI Chat Orchestration Protocol v1

Status: control-loop optimization contract; observer-only with respect to the accepted execution-policy/P5 runtime path.

## Purpose

This contract defines how a ChatGPT executor should drive an opted-in GitHub Actions
Lambda lane with the fewest safe model-visible interactions and without routine human relay.

The owning execution-policy/P5 task remains authoritative for workload selection,
security boundaries, exact-SHA admission, validation/acceptance evidence, host/runtime
policy, trusted-cache policy, runner cleanup, and CPU/GPU/model workload decisions.
This protocol observes and optimizes only the ChatGPT/GitHub orchestration path.

It sits above the self-hosted execution implementation:

ChatGPT
-> GitHub connector
-> pull request / trusted issue-comment trigger
-> trusted project workflow
-> self-hosted runner demand
-> controller/provisioner implementation owned by the parent task
-> one-job isolated runner
-> GitHub run / artifact evidence
-> ChatGPT continuation

The chat executor does not call the root provisioner socket, construct JIT
configuration, select UID/GID, choose filesystem paths, select GPU device nodes,
or supply arbitrary systemd properties. Those are infrastructure policy owned
below this layer.

## Observed GitHub connector surface

The connected ChatGPT GitHub surface can:

- inspect PRs, branches, commits, issue comments, workflow runs, jobs, steps,
  logs, and workflow artifacts;
- add a top-level PR Conversation comment;
- rerun a failed workflow run or a selected job;
- mutate an authorized branch/PR when the owning task permits it.

The current surface does not expose a direct workflow-dispatch operation.

The accepted research-engine Lambda workflows already use owner-only
issue-comment triggers with an exact candidate SHA. Therefore the normal chat
trigger is the existing trusted comment command, not a new privileged RPC.

## Security and ownership boundary

The ChatGPT-facing request contains only project/workflow-level facts:

- repository;
- PR number;
- exact candidate SHA;
- trusted workflow identity;
- accepted trigger verb;
- non-secret correlation metadata.

The following must never be chat-supplied privilege inputs:

- JIT configuration;
- root socket request bodies;
- runner UID/GID;
- host paths;
- device nodes;
- network rules;
- systemd properties;
- controller credentials;
- GitHub App private keys.

P5 remains authoritative for converting trusted GitHub job demand into safe local
runner supply. This protocol treats that mechanism as opaque infrastructure.

## Run handle

Before triggering a Lambda lane, bind a compact non-secret run handle conforming
to 'architecture/lambda-ci-chat-run.v1.schema.json'.

The handle records the exact PR head, workflow, actor, trigger comment ID/time,
pre-trigger workflow run number, and expected receipt artifact. It is the
correlation state for the chat control cycle, not a new project authority.

## Trigger sequence

1. Fetch the PR and bind its current 40-character head SHA.
2. Read the latest run number for the intended workflow before triggering.
3. Add exactly one trusted issue comment for that SHA.
4. Record the returned comment ID and creation time.
5. Do not post another trigger while the first request is unresolved unless
   evidence proves the first trigger did not create a run.

Candidate mutation after step 3 invalidates the request. A changed PR head
requires a new trigger bound to the new SHA; never silently rerun stale candidate
work.

## Correlation model

Issue-comment workflow runs expose the repository default-branch SHA rather than
the requested candidate SHA. Therefore run.head_sha is not candidate identity.

### Provisional run binding

After one trusted exact-SHA trigger, a run may be bound provisionally when
exactly one post-trigger run satisfies:

- exact workflow path;
- event is issue_comment;
- triggering actor matches;
- run number is greater than the pre-trigger baseline;
- run creation is not earlier than the trigger comment.

If zero runs match, wait for a run. If more than one matches, fail closed as
AMBIGUOUS rather than selecting the newest run.

### Exact P5 job-identity confirmation

For current P5 CPU/gpu-small workflows, the job name already binds the workload,
PR number, trigger verb, and exact requested SHA:

    wc-admission-v1|workload=<workload>|pr=<pr>|request=<trigger-command> <sha>

One job-detail read can therefore upgrade a provisional run binding to exact
model-visible request correlation when exactly one job name equals the expected
identity. A mismatched workload, PR, trigger command, or SHA is not accepted.
Multiple exact matches are ambiguous and must fail closed.

This job identity is correlation evidence only. Terminal success still requires
the compact receipt to prove PR number, expected SHA, actual SHA when present,
and PASS.

An immutable issue-comment ID embedded in run metadata remains a possible future
ergonomic improvement for distinguishing duplicate identical trigger comments,
but it is not a prerequisite for ordinary one-trigger-per-candidate P5
orchestration. Do not modify a project workflow solely to collect optimization
telemetry.

## Observation ladder

Use the cheapest evidence source that can change the next decision.

### Run queued

Read only high-level run state by default.

Do not fetch logs. A single job read is justified only when a prolonged queue
must be distinguished between no runner assignment and assigned-but-not-started
execution.

State: WAIT_EXTERNAL / runner allocation.

### Run in progress

Do not repeatedly fetch logs merely to show activity. The run is active compute,
so it is a legitimate external wait.

Fetch job/step detail only when it changes a decision, such as diagnosing an
unexpectedly stalled stage.

State: WAIT_EXTERNAL / compute.

### Run completed successfully

Terminal status is actionable immediately.

1. list the expected compact artifact;
2. download/read the receipt;
3. verify PR number, expected candidate SHA, actual SHA when present, and PASS;
4. continue the owning task immediately.

Do not remain in a thought/wait loop after terminal evidence exists.

### Run completed unsuccessfully

1. fetch jobs;
2. fetch step summaries for the failing job;
3. fetch full logs only for the failing job/stage when summaries are insufficient;
4. consume the compact receipt when available;
5. classify the failure before deciding whether to repair candidate code,
   repair infrastructure through the parent owner, or rerun unchanged work.

Avoid downloading every log or artifact by default.

## Rerun policy

A rerun is safe only when the exact candidate SHA and relevant policy inputs have
not changed.

- transient runner/infrastructure failure with unchanged candidate: rerun the
  failed job/run if the owning workflow permits it;
- candidate code changed: post a new exact-SHA trigger comment;
- workflow/profile/policy changed: obtain a new trigger under the new validated
  state;
- ambiguous prior execution: inspect actual durable state before any retry.

Never use rerun as a substitute for diagnosing a demonstrated deterministic
failure.

## Receipt acceptance

A successful GitHub conclusion alone is insufficient for a provisionally
correlated issue-comment run.

The receipt must match:

- PR number;
- requested candidate SHA;
- actual checkout SHA when that field exists;
- decision PASS.

A mismatch is REJECT_EVIDENCE, not a soft warning.

## Chat/task persistence

Ordinary short waits do not require a task-capsule mutation.

Before a long external wait, executor handoff, or conversation boundary, persist
only the compact run identity needed for recovery: repository, PR, candidate SHA,
workflow, run ID/attempt if bound, last terminal/nonterminal state, and first next
operation.

Do not copy giant logs into task state.

## Concurrent-chat and Heartbeat rule

Workspace Heartbeat v0.4.4 enforces task/conversation ownership in the backend.
For a substantial assistant response, call heartbeat_begin_turn once for this
optimization task, carry its opaque turn_id on later heartbeat_update calls, and
never write the owning P5/execution-policy task's heartbeat stream.

Distinct task IDs may progress concurrently. Cross-conversation writes to one
active task fail closed. This separates progress-channel ownership from durable
task authority and prevents the collision mode observed during the original P5
bring-up.

## Model-visible control-loop target

Count one GitHub read for each assistant-visible GitHub connector/tool invocation
used for run discovery/binding, status, job detail, logs, or artifact retrieval.
Do not estimate or count hidden REST/API requests performed inside a connector.

Count human relay only when the user actually performs a terminal, SSH, sudo, or
credential action for that run. Preserve null for timestamps or facts that were
not naturally observed.

For an ordinary successful P5 CPU/gpu-small run:

1. bind the post-trigger run provisionally with the minimum necessary run read;
2. confirm exact workload + PR + request SHA through the existing job identity;
3. while nonterminal, perform only bounded status reads that can change the next
   decision;
4. once terminal success is observed, retrieve the compact receipt/artifact;
5. verify exact candidate identity and PASS;
6. immediately continue the owning task.

Do not fetch full logs on the ordinary success path. Do not perform SSH/sudo or
host-side inspection solely for optimization measurement.

If the owning task requires additional acceptance, recovery, cleanup, or safety
evidence, classify those reads/actions as REQUIRED_ACCEPTANCE_RECOVERY_EVIDENCE.
They are not orchestration inefficiency and must not be optimized away.

Artifact discovery and artifact-byte retrieval may require more than one visible
connector invocation on the current tool surface. Count the invocations actually
used rather than pretending they are one abstract read.

## Acceptance metrics

Measure from naturally required runs:

- model-visible GitHub reads by category: run binding, status, job detail, full
  logs, artifact;
- human terminal/SSH/sudo/credential relay actually required for the run;
- ambiguous correlation rate;
- full-log downloads on successful runs;
- terminal_evidence_first_available_at;
- receipt_validated_at;
- next_substantive_action_started_at.

The primary latency metric is:

    terminal GitHub evidence -> compact receipt validated -> next substantive action

Targets for ordinary successful runs are:

- exact job/request correlation without hidden head_sha assumptions;
- zero routine human relay;
- zero full-log reads;
- one compact receipt validation path;
- the minimum status reads needed for a 10-20 second Lambda run;
- immediate continuation after terminal receipt validation.

A null continuation timestamp remains null; do not infer latency from absent
evidence.

## Migration rule

Do not change the parent P5 controller/provisioner implementation from this
protocol task.

Keep implementation changes owned by this optimization task and limited to the
chat-facing protocol/reducer/tooling. The accepted P5 runtime and project workflow
remain externally authoritative. Adopt additional run metadata only if a real
correlation ambiguity demonstrates that the existing exact job identity is
insufficient.
