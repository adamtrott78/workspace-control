# Shared Operator Workflow

Status: **provisional bridge v0.1**

## Purpose

This policy owns the cross-project operating contract for work performed in the
workspace under `~/adamArchives/Adam`.

It generalizes the mature ChatGPT ↔ terminal ↔ Git/GitHub workflow that was
originally developed inside PADataset, while remaining compatible with agentic
executors such as Codex and connected ChatGPT tools.

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

## Execution modes

The workflow supports multiple execution modes. The mode changes **who performs
the operation**, not the evidence or validation standard.

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

### 3. HYBRID

Use when some operations are best performed directly and others require the
prepared local runtime.

Typical pattern:

```text
direct GitHub/context edit
→ local Lambda build or experiment
→ returned artifact/log evidence
→ direct GitHub persistence
```

Each transition MUST preserve repository identity and synchronization.

### 4. READ_ONLY

Use when the task forbids mutation, is a cold-start evaluation, or does not yet
have sufficient authority/evidence to change state.

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

## Task capsules and executor handoff

Long-running, cross-repository, or executor-switchable work SHOULD use the
workspace-control task-capsule mechanism.

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

## Compatibility bridge

This policy is initially a copy/refinement of workflow principles proven in
PADataset and the MTH 602 tutor evaluation.

PADataset is intentionally left unchanged during this bridge phase.

The eventual context/control-plane refactor may replace duplicated PADataset
operator text with a route to this shared owner only after cold-start and
cross-executor validation demonstrate that doing so is safe.

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
- ChatGPT+human → Codex handoff.

Failures should be classified as routing, content, implementation, evidence, or
executor-portability defects.
