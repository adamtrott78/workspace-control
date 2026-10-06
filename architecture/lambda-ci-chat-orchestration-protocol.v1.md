# Lambda CI Chat Orchestration Protocol v1

Status: parallel optimization contract; does not change the accepted P2-P5 runtime path.

## Purpose

This contract defines how a ChatGPT executor should drive an opted-in GitHub Actions
Lambda lane with the fewest safe tool calls and without routine SSH.

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

## Strong correlation mode

Issue-comment workflow runs report the repository default-branch SHA rather than
the requested candidate SHA. The current run metadata also does not directly
expose the triggering issue-comment ID.

Opted-in project workflow adapters should therefore set run display metadata that
contains the immutable GitHub issue-comment ID. A recommended run-name convention
is:

    <lane-name> PR #<issue-number> comment:<github.event.comment.id>

ChatGPT already receives the created comment ID from the connector, so this gives
an exact non-secret correlation key without changing the privilege boundary or
candidate checkout contract.

This optimization branch does not modify the research-engine workflow while P5
is active. The metadata convention is a project-adapter follow-up after the
parent path is stable.

## Compatibility correlation mode

Until a workflow exposes comment-ID metadata, fail closed.

A run may be bound provisionally only when exactly one run satisfies all of:

- exact workflow path;
- event is 'issue_comment';
- triggering actor matches;
- run number is greater than the pre-trigger baseline;
- run creation is not earlier than the trigger comment;
- display title equals the PR title used by the trigger.

If zero runs match, the next state is WAIT_FOR_RUN.

If more than one run matches, the state is AMBIGUOUS. Do not guess based on
newest-run ordering.

A provisionally correlated run is not terminal evidence. Its receipt must later
prove the exact PR number and candidate SHA before success is accepted.

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

Workspace Heartbeat is a single-writer progress stream per task_id.

When two ChatGPT conversations are simultaneously active around the same durable
task, exactly one conversation may own heartbeat_open / heartbeat_update for that
task_id. Observer/adjacent optimization chats must not write to the same
heartbeat stream.

Writer ownership transfers explicitly at handoff. Merely opening another chat
does not grant a second writer lease.

This prevents one conversation from overwriting, reordering, or semantically
polluting another conversation's live progress card.

This rule does not prevent read-only observation of the parent task through
GitHub. It separates progress-channel ownership from durable task authority.

## Tool-call target

For the common successful path after P5 acceptance, the target interaction is:

- resolve PR + current SHA;
- record pre-trigger workflow run baseline;
- post one trusted trigger comment;
- bind one run;
- perform bounded run-state reads while compute is active;
- on terminal success, fetch artifact metadata and the compact receipt;
- continue immediately.

No SSH, sudo relay, PAT copy/paste, controller socket interaction, or broad log
download belongs in the normal chat loop.

## Acceptance metrics

Measure at least:

- human terminal steps per Lambda run;
- GitHub tool calls from trigger to bound run;
- GitHub tool calls from terminal run to actionable diagnosis;
- ambiguous-run correlation rate;
- full-log downloads per successful run;
- time spent waiting after a run was already terminal;
- number of repeated trigger comments for one candidate SHA.

Target values after P5 plus strong correlation:

- zero routine human terminal steps;
- zero ambiguous correlations;
- zero full-log downloads on success;
- immediate continuation after terminal receipt validation;
- one trigger comment per candidate/lane attempt.

## Migration rule

Do not change the parent P5 controller/provisioner implementation from this
protocol task.

First validate this chat-facing state machine and correlation policy in
workspace-control. Then, after the parent execution path is stable, project-owned
workflow adapters may adopt the metadata-only comment-ID run-name convention.
