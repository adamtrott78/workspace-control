# Shared Operator Workflow

Status: **v2 candidate**

## Purpose

This policy owns the cross-project operating contract for work performed in the
workspace under `~/adamArchives/Adam`.

It generalizes the proven ChatGPT/direct-tool, human-terminal, browser-ingress,
local-runtime, and Codex workflows while remaining executor-neutral.

This file governs **how work is executed and synchronized**. It does not own
project-specific scientific, course, assignment, artifact, or implementation
truth.

Project repositories remain authoritative for their own domain contracts and
must route here when cross-project operator behavior is needed.

## Core principle

Changing executors may change the degree of automation, but it must not change
the workflow's evidence, validation, authority, or synchronization semantics.

The canonical loop is:

```text
route to authority
→ inspect actual state
→ choose bounded mutation scope
→ execute using an authorized mode
→ validate produced state/artifacts
→ inspect targeted diff
→ narrow staging/commit
→ push/verify remote identity
→ reread pushed state
→ reroute if task ownership changes
```

A proposed, generated, inspected, or explained operation is not evidence that it
executed.

## Continuation obligation

An authorized executor MUST continue advancing a task while a safe, in-scope
operation surface remains available.

A chat turn, commit boundary, successful substage, convenient stopping point, or
desire to summarize is **not** a suspension boundary.

The executor may stop/suspend only when at least one of these is true:

1. **Unavailable execution capability** — the next required operation genuinely
   cannot be performed through any currently authorized direct tool, connected
   executor, repository surface, or available runtime.
2. **Required human judgment or approval** — the owning workflow explicitly
   requires a user decision, visual/subjective judgment, approval, credential
   action, physical-world action, or other human-owned input before continuation.
3. **Authority/safety boundary** — continuation would exceed mutation authority,
   risk unrelated work, require a destructive/externally consequential action
   without approval, or violate an owning contract.
4. **Missing irreducible input** — required source bytes/data/hardware are not
   available to any current executor and cannot be retrieved through an
   authorized surface.

Before declaring a runtime/local boundary, the executor MUST check whether the
operation can instead continue through another authorized surface. For example,
a container network failure is not a task boundary when a connected scholarly
tool can still complete the next scientific step; conversely, exact byte hashing
is a genuine boundary when only the user's local filesystem contains the bytes.

When suspension is necessary, durable task state MUST record:

- the exact unavailable capability or required human decision;
- why currently available surfaces cannot satisfy it;
- the smallest resume condition;
- the first safe operation after resume.

If another authorized operation can still make meaningful progress without
invalidating the blocked step, perform that work before suspending.


## Authority boundary

This policy owns shared rules for:

- repository/worktree state inspection;
- dirty-work protection;
- human-terminal execution;
- direct connected-tool execution;
- copy/paste and shell safety;
- artifact validation;
- visual/human review gates;
- Git staging, commits, pushes, and synchronization;
- cross-executor continuation;
- mid-conversation task rerouting.

It does **not** determine:

- what a course assignment requires;
- what a research experiment means;
- what mathematical result is correct;
- what files a project considers normative;
- what mastery evidence a tutor should record;
- what an application or report should contain.

Those decisions belong to the project/domain owner.

## Routing is continuous, not startup-only

Routing is not a one-time initialization step.

Whenever work materially changes task ownership, the executor MUST pause before
acting and load the new owning context.

Examples:

```text
tutoring
→ learning-record persistence

learning-record persistence
→ report construction

report construction
→ code execution

analysis
→ experiment launch

experiment execution
→ result interpretation

local project work
→ cross-project coordination
```

A conversation that began under one owner does not retain mutation authority for
a later, materially different task merely because it is the same conversation.

The normal transition rule is:

1. identify that the task owner changed;
2. return to the project routing entry point;
3. load the new local owner;
4. load this shared operator policy when mutation/runtime coordination is involved;
5. inspect actual state before acting.

## Operation surfaces and execution topology

The bridge labels below remain useful operating shorthands, but v2 distinguishes
reasoning executor, operation surface, and execution topology.

The selected surface/topology changes **how an operation is performed**, not the
authority, evidence, or validation standard.

### 1. HUMAN_TERMINAL

Use when ChatGPT is directing a human-operated terminal or when direct mutation
tools are unavailable or intentionally disabled.

The assistant SHOULD provide one bounded copy/paste operation at a time.

The user executes it on the prepared machine and returns exact evidence such as:

- stdout/stderr;
- exit status;
- logs;
- `git status`;
- generated artifacts;
- hashes;
- screenshots or rendered pages.

The assistant MUST NOT describe the operation as executed until evidence is
returned.

For long operations, use a child shell or tracked script rather than enabling
strict mode in the user's persistent login shell.

### 2. DIRECT_TOOL

Use when the executor has an authorized connector, agent, filesystem, GitHub, or
other mutation tool and the task/project permits direct execution.

The executor MAY make bounded edits, commits, and pushes directly without first
turning every mutation into Bash for the user.

Direct execution MUST still satisfy the same contracts:

- establish repository/ref identity;
- establish intended mutation scope;
- protect unrelated work;
- make bounded changes;
- validate the result;
- inspect the actual diff;
- commit only reviewed scope;
- verify the pushed remote state;
- reread the pushed state before the next tracked mutation.

Connected-tool convenience does not waive evidence discipline.

### 3. COMPOSED / HYBRID

Use when required state or capabilities span multiple operation surfaces or
locations. "HYBRID" is a compatibility shorthand for composed topology, not a
single executor type.

Typical pattern:

```text
direct GitHub/context edit
→ local Lambda build or experiment
→ returned artifact/log evidence
→ direct GitHub persistence
```

Each transition MUST preserve repository identity and synchronization.

### 4. READ_ONLY

READ_ONLY is primarily an intent/authority state rather than an executor type.
Use it when mutation is forbidden, the task is a cold-start evaluation, or
sufficient authority/evidence to change state does not yet exist.

## Mutation authority

Execution capability and mutation authority are separate.

A tool being able to write a repository does not itself authorize the write.

Mutation authority should come from one of:

- an explicit user instruction;
- a project-local context that grants a defined class of automatic updates;
- a durable task capsule with mutation intent and allowed scope;
- an already approved bounded plan.

When authority is broad enough for repeated low-risk updates, the executor need
not ask for confirmation before every individual file edit.

Examples include a tutor that is explicitly allowed to maintain learning/mastery
records as evidence is produced.

High-impact, ambiguous, destructive, or externally consequential actions still
require the approval rules of their owning workflow.

## Preflight before mutation

Before mutating a prepared repository/worktree, establish the relevant:

- logical repository identity;
- checkout/worktree path when local execution is involved;
- branch/ref;
- current HEAD;
- dirty state;
- staged state;
- untracked state when relevant;
- remote identity and expected branch;
- intended mutation scope;
- required runtime/environment/hardware state.

For a human-operated local checkout, the minimum inspection normally includes:

```bash
pwd
git branch --show-current
git rev-parse HEAD
git status --short
git diff --stat
git diff --cached --stat
git ls-files --others --exclude-standard
```

Do not infer checkout identity from an already-open Jupyter browser, remembered
path, editor window, or previous conversation.

## Dirty-work protection

Executors MUST NOT automatically:

- clean;
- reset;
- stash;
- switch branches;
- overwrite unrelated files;
- delete unrelated artifacts;
- broadly stage unrelated work

merely to normalize a checkout.

If unrelated work makes mutation unsafe, prefer an isolated branch/worktree or
another explicitly reviewed boundary.

A dirty checkout is not automatically unusable. It requires inspection and an
explicitly safe mutation plan.

## Direct GitHub mutation and local checkout coordination

Direct remote writes can make a prepared local checkout stale.

Before directly mutating a branch that may also be used on Lambda:

1. establish the expected remote branch/commit;
2. avoid the write when known local unpushed work could conflict;
3. make the remote mutation on a bounded branch/ref;
4. verify the resulting remote commit;
5. before the next local mutation, re-inspect the local checkout and synchronize
   intentionally.

Do not assume a local checkout moved merely because GitHub changed.

Do not automatically force/reset the local checkout to the remote state.

## Bounded operations

A bounded operation has:

- one clear objective;
- an explicit repository/ref;
- an explicit file or artifact scope;
- known preconditions;
- defined validation;
- a stop condition.

Prefer several bounded operations over one opaque mega-operation when failures
would otherwise be hard to diagnose.

When a workflow has substantial state, retries, concurrency, monitoring,
recovery, or repeated use, prefer a reusable tracked `.sh`, `.py`, `.m`, or
other owned procedure rather than a long sequence of ephemeral commands.

A one-off text edit does not require a permanent script merely because Bash can
perform it.

## Interactive-shell safety

Commands intended for a user to paste into an **existing interactive shell or SSH
session MUST NOT change failure-control options in that parent shell**.

In particular, do not emit a block whose first operation is:

```bash
set -e
set -euo pipefail
```

when the block is expected to run directly in the user's current interactive
shell. A later noncritical command failure can terminate that shell and, over
SSH, disconnect the session.

For bounded fail-fast execution, run the body in a child shell instead:

```bash
bash -lc '
set -euo pipefail
# bounded commands
'
rc=$?
echo "COMMAND_BLOCK_RC=$rc"
```

or use an equivalent subshell/function whose shell options do not leak into the
parent interactive session.

Rules:

- the parent interactive/SSH shell SHOULD survive ordinary command failure;
- fail-fast behavior belongs inside the bounded child execution context;
- a diagnostic/reporting command failing after the required mutation succeeded
  MUST NOT erase evidence of the successful mutation;
- after any failure, inspect durable state before retrying a mutation;
- when the child exits nonzero, print/return the exit status and relevant
  evidence instead of relying on the SSH session disappearing as a failure
  signal.

Noninteractive scripts executed as their own process MAY use
`set -euo pipefail` normally because their exit does not terminate the user's
parent interactive shell.

## Scratch and human-transfer artifacts

Use `/tmp` only for executor-internal ephemeral scratch that the human does not
need to locate, upload, inspect, or carry across executor boundaries.

When an operation will produce a file the user must access, prefer the shared
workspace scratch root:

`~/adamArchives/Adam/.workspace-control/tmp`

Executors SHOULD honor `WORKSPACE_CONTROL_SCRATCH_ROOT` when set; otherwise the
workspace path above is the default for this environment.

Create task-specific subdirectories beneath that root rather than dropping files
directly into `~/adamArchives/Adam`.

A command that produces a human-transfer artifact SHOULD print its final absolute
path and hash/identity. Do not force the user to copy an artifact out of
`/tmp` merely because the executor chose an inaccessible scratch location.

Project-owned durable outputs still belong in their owning repository/artifact
location; the shared scratch root is a transfer/staging area, not a new source of
truth.

## Human-terminal command integrity

Copy/paste integrity is part of the workflow.

If a command is supplied for human execution:

- every shell line must visibly remain inside one code fence;
- embedded Markdown fences must not terminate the outer command block;
- the user should not reconstruct a broken command from prose;
- large strict-mode operations should run inside a child `bash`, subshell, or
  tracked script.

Do not enable `set -e` or `set -euo pipefail` directly in a long-lived SSH
login shell for a large assistant-supplied operation.

## Execution evidence

Claims about execution MUST be grounded in observable evidence.

Useful evidence includes:

- exact stdout/stderr;
- exit code;
- generated file existence;
- file hashes;
- logs;
- Git diffs;
- commit SHAs;
- remote refs;
- saved configuration;
- result records;
- rendered pages;
- runtime metadata.

A command appearing in chat is not execution evidence.

An executor saying that it ran something is not sufficient when the environment
provides a stronger inspectable record.

## Artifact validation

Process exit status is necessary but may not be sufficient.

The owning project should define what makes an artifact valid.

Depending on the task, validation can include:

- structural/static checks;
- unit or numerical tests;
- dimensions/shapes;
- semantic invariants;
- reproducibility records;
- build logs;
- freshness checks;
- visual inspection;
- scientific/data contracts;
- provenance and hashes.

Examples:

- a PDF surviving from an earlier build is not proof the latest LaTeX compiled;
- a checkpoint existing is not proof of its dataset/configuration;
- a notebook containing output is not proof current source generated it;
- a plot rendering is not proof the underlying numerical record is correct.

## Validation routing and CI cost discipline

Before launching CI or another expensive validation path for a tracked mutation
governed through workspace-control, the executor MUST establish the exact changed
path set and route validation deliberately.

When the owning repository has a reviewed validation profile, use the shared
planner/procedure in `procedures/validation_routing.md` before starting CI. The
selected tier is a lower bound on required evidence, not permission to ignore an
owning workflow's stronger requirement.

When no reviewed project profile exists, when the planner/profile cannot be
resolved, or when dependency/risk radius is ambiguous, preserve the owning
project's existing/full validation. Do not infer a cheaper tier from model
judgment alone.

Cheap deterministic preflight SHOULD happen before opening a pull request. One
logical mutation SHOULD be batched into one reviewed Git checkpoint where the
operation surface permits it, rather than drip-fed as unrelated file commits.

While external CI runs, status reads SHOULD occur at decision points rather than
tight polling intervals. Prefer high-level run state first, job detail only when
needed, and logs only for diagnosis.

A passed pull-request check MAY unblock subsequent work without synchronously
waiting for a duplicate canonical run only under the tested-tree conditions in
`procedures/validation_routing.md`. Post-submit, scheduled, deployment, release,
or other canonical-only validation remains authoritative whenever those
conditions do not hold.

## Human review gates

Some correctness properties are inherently visual, subjective, or user-owned.

The owning workflow MAY require a human gate for:

- final report/page layout;
- figures;
- slide decks;
- images;
- externally submitted artifacts;
- other user-facing deliverables.

When such a gate is required, the executor MUST stop before completion
bookkeeping that depends on approval.

An agent MAY perform preliminary visual QA itself when tooling allows, but that
does not silently replace a required human approval gate.

## Git review and staging

For tracked changes, prefer:

```text
working diff
→ diff/check validation
→ reviewed path set
→ narrow staging
→ cached diff/check validation
→ commit
```

Avoid broad `git add .` in prepared research/coursework repositories when
unrelated files may exist.

Changed-path validation SHOULD be order-independent. Treat the file collection as
a set unless ordering is itself meaningful.

Do not fail validation merely because Git reports the same expected files in a
different order.

## Commit boundaries

Commits should represent meaningful durable checkpoints, not arbitrary chat
turns.

Good boundaries include:

- learning evidence persisted;
- one assignment problem/report section completed;
- experiment configuration added;
- reproducible analysis completed;
- final artifact validated;
- mastery promotion recorded.

A connected executor MAY commit and push directly when authorized.

The workflow does not require the human to execute Git commands merely for the
sake of human execution.

## Push and synchronization

After a tracked checkpoint:

1. push the intended branch;
2. resolve the local/direct commit SHA;
3. resolve the advertised remote branch SHA;
4. require equality when the workflow expects synchronization;
5. reread the pushed GitHub state before the next tracked mutation.

GitHub is the synchronization point for tracked state.

Ignored/local runtime artifacts require their own provenance and cannot be
recovered merely from a Git commit.

## Reread requirement

After pushing a tracked mutation, an executor SHOULD reread the exact pushed
commit or files it intends to rely on next.

This catches:

- stale conversational assumptions;
- partial writes;
- wrong branches;
- unexpected file content;
- divergence between proposed and actual state.

The next mutation should be based on durable pushed state rather than private
conversation recollection.

## Smart recovery restore points

Long-running durable tasks SHOULD maintain a lightweight rolling recovery point
inside the existing task capsule.

The purpose is fast recovery after stream loss, executor throttling, chat limits,
or an interrupted tool cycle. A restore point is an **index into authoritative
durable state**, not another source of truth.

Use one stable checkpoint entry such as:

```text
id: restore-point:latest
kind: recovery_restore_point
required_for_resume: true
```

Refresh that entry only at high-value semantic boundaries:

- after a validated stage, merge, or scientific/implementation slice changes
  the correct resume basis;
- immediately before launching a long external runtime, CI job, experiment, or
  other operation likely to outlive the current response cycle;
- before an executor/surface handoff or required human/local boundary;
- after resolving an ambiguous failure or concurrent-state conflict, once a new
  known-good state has been verified;
- after a substantial batch of work when the next operation begins a materially
  different slice.

Do **not** refresh it:

- after every tool call;
- after ordinary read-only inspection;
- for every poll of the same external run;
- after an intermediate commit that has not yet been validated;
- merely because a chat turn is ending.

A useful restore point records, compactly:

- the exact primary resume commit/ref;
- current stage;
- any in-flight branch / PR / external run identity that matters;
- the last completed validation boundary;
- the first safe next operation.

The active task capsule's normal repository, stage, blocker, remaining-work, and
`next_safe_action` fields remain authoritative. The restore point MUST NOT
duplicate large histories or embed transient logs.

For tasks with a derived Markdown handoff, refreshing the restore point is a
material capsule mutation and therefore follows the normal atomic JSON ->
Markdown synchronization invariant.

Prefer replacing the single rolling restore-point entry over appending one
checkpoint per operation. Historical scientific/implementation checkpoints
remain separate immutable evidence; the rolling restore point exists only to
accelerate recovery.

## Failure handling

On a failed guard or validator:

- do not blindly rerun a mutation that may already have applied;
- inspect actual state first;
- distinguish mutation failure from validation failure;
- prefer a smaller read-only diagnostic;
- repair only the demonstrated defect.

Validators should avoid brittle assumptions such as incidental file ordering or
extra trailing blank lines unless those properties are genuinely part of the
contract.

## Workflow descriptors, task capsules, and executor handoff

Reusable project procedures MAY expose a project-owned workflow descriptor.

Long-running, cross-repository, suspended/resumable, or executor-switchable work
SHOULD use the workspace-control task-capsule mechanism.

A workflow descriptor states how a class of task works. A task capsule states
where one execution currently is. When a capsule depends on a workflow or shared
contract, it should pin the exact durable version.

The capsule should record:

- repositories and refs;
- mutation scope;
- pushed checkpoints;
- executed operations;
- artifacts;
- validation;
- blockers;
- remaining work;
- next safe action.

A handoff should not depend on a special prose explanation if the normal
workspace-control entry route and durable state are sufficient.

When an active capsule maintains a derived
`tasks/active/<task_id>.md` handoff, a material JSON state change and the
Markdown regeneration form one control-cycle unit. The executor MUST regenerate
the Markdown from the post-mutation JSON before performing another task
operation or handing the task to a new conversation/executor. A stale companion
Markdown is a synchronization defect, not an acceptable steady state.

See `procedures/task_capsule.md`.

## Project integration contract

A managed project that uses this shared workflow SHOULD:

1. keep its project/domain truth in its own repository;
2. expose a root routing entry point;
3. route shared operator concerns to this policy;
4. retain project-local operator context only for project-specific details;
5. reroute when task ownership changes mid-conversation;
6. define artifact-specific validation locally.

A project-local operator file may supplement this policy but should not fork or
silently redefine the shared execution semantics.

## Evidence lineage

This policy incorporates principles independently demonstrated through PADataset,
MTH602, EAS501, CIS560 architecture experiments, and Codex handoff testing.

Those project repositories remain independent authorities. Integration of shared
policy does not itself migrate their local contexts.

## Acceptance tests

The shared workflow is not fully validated merely because this document exists.

Representative tests should include:

- fresh project startup;
- mid-conversation owner transition;
- clean and dirty checkout cases;
- HUMAN_TERMINAL execution;
- DIRECT_TOOL execution;
- local-runtime + remote-tool HYBRID execution;
- artifact build plus human visual gate;
- narrow staging/commit/push;
- post-push reread;
- Codex → ChatGPT+human handoff;
- ChatGPT+human → Codex handoff;
- premature-suspension regression: executor continues across available direct/
  composed surfaces and suspends only at a demonstrated capability, approval,
  authority, or irreducible-input boundary;
- human-transfer scratch regression: user-accessible artifacts are emitted under
  the configured workspace scratch root rather than requiring a manual copy out
  of `/tmp`;
- interactive-shell safety regression: a failing command inside a user-pasted
  SSH block returns a visible nonzero child status without terminating the
  parent interactive shell.

Failures should be classified as routing, content, implementation, evidence, or
executor-portability defects.
