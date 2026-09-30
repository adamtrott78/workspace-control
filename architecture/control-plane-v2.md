# Workspace Control Plane v2 Architecture

Status: **draft for review**

Branch: `control-plane-v2-refactor`

Base: `cb8368cd50de2d364c2aade8843276aab0b02420`

## Purpose

Workspace Control Plane v2 generalizes the proven workspace-control, tutor, Codex,
DIRECT_TOOL, human-gate, and PADataset/MILCOM workflow evidence into one
executor-neutral architecture for durable multi-stage work.

The control plane coordinates work. It does not become a super-repository and
does not absorb project-domain truth.

The core design objective is:

> more verified stages per autonomous control cycle

A single assistant response may span several tools or execution surfaces, but
each material stage remains independently bounded, validated, and recoverable.

## Evidence basis

This design is informed by independently observed workflows:

- Phase-3 workspace-control established registry, preflight, durable task
  capsules, and deterministic handoff assessment.
- Phase-4 proved ChatGPT -> durable task state -> Codex execution and
  Codex -> durable evidence -> fresh ChatGPT recovery.
- MTH602 proved conservative repository-backed tutoring, automatic
  pedagogical persistence, deadline-driven completion without false mastery,
  and later mastery recovery.
- EAS501 proved DIRECT_TOOL empty-repository bootstrap, remote Git lifecycle
  management, browser-mediated existing-byte ingress followed by DIRECT_TOOL
  verification, genuine cold-start tutoring, and inline persistence followed by
  return to live tutoring.
- CIS560 supplied independent evidence for typed authority and defined
  experiments for Gmail -> Git -> parent return, idempotent re-entry, JFLAP
  suspension/resume, atomic multi-file DIRECT_TOOL mutation, and composed
  workflow validation.
- MILCOM/PADataset proved practical orchestration across remote Git mutation,
  exact pushed checkpoints, isolated local worktrees, local rendering/build
  execution, artifact validation, human visual review, and return to source
  repair.

External systems such as durable workflow engines, graph orchestrators,
agent/workflow frameworks, GitOps, and asset-oriented orchestrators are design
references only. They are not canonical dependencies of workspace-control.

---

# 1. Architectural layers

The intended architecture is:

```text
project-local domain authority
        |
        v
shared behavioral / portability contracts
        |
        v
workspace coordination + durable task state
        |
        v
thin executor adapters / routing
        |
        v
reasoning executors + operation surfaces
```

These layers have different authority.

## 1.1 Project-local domain authority

Each project repository remains authoritative for its own:

- scientific or course truth;
- implementation truth;
- source provenance;
- artifact semantics;
- workflow-specific validation;
- project-owned deterministic procedures;
- project-owned workflow descriptors.

workspace-control MUST NOT silently replace these owners.

## 1.2 Shared contracts

workspace-control owns reusable cross-project semantics such as:

- executor portability;
- shared operator behavior;
- routing and rerouting;
- mutation evidence discipline;
- task coordination;
- failure/recovery expectations;
- handoff semantics;
- generic workflow/stage vocabulary.

Course-specific tutoring behavior may remain in a shared tutoring contract when it
is intentionally reusable across course repositories, but course facts remain
local.

## 1.3 Workspace coordination

workspace-control coordinates:

- logical repository identity;
- mutation policy;
- current task execution state;
- cross-repository task state;
- checkpoint identity;
- executor/surface handoff;
- topology-aware preflight;
- resumability;
- safe worktree preparation;
- deterministic validation of generic control-plane invariants.

## 1.4 Thin executor adapters

Executor-specific mechanisms such as:

- Codex `AGENTS.md`;
- Skills;
- ChatGPT tool-routing helpers;
- other future adapters

MUST route to canonical contracts and procedures.

They MUST NOT become competing sources of project, workflow, artifact, or
scientific truth.

## 1.5 Executors and operation surfaces

The architecture MUST distinguish the reasoning actor from the mechanism used to
perform an operation.

No executor or surface is globally trusted merely because it is capable of
mutation.

---

# 2. Core definitions

## 2.1 Owner

An **owner** is the authoritative source for a specific class of truth or
decision.

Ownership is typed, not necessarily hierarchical.

Examples:

- assignment file -> assignment requirements;
- textbook -> formal theorem statement;
- `.jff` file -> saved automaton structure;
- runtime log -> what executed;
- experiment manifest -> dataset/run identity;
- report source -> report composition;
- Git ref -> durable repository checkpoint;
- behavioral tutoring record -> student mastery evidence.

A source may outrank another for one fact type without globally outranking it.

## 2.2 Workflow

A **workflow** is a reusable project-owned procedure for accomplishing a class of
task.

A workflow describes stable procedure, not current progress.

It MAY define:

- entry route;
- relevant owners;
- stages;
- stage dependencies;
- deterministic project commands;
- expected artifacts;
- artifact classes;
- validation;
- permitted human/tool gates;
- forbidden mutation areas.

A workflow descriptor is not a task capsule.

## 2.3 Stage

A **stage** is a bounded unit of workflow execution.

A material stage SHOULD establish, as applicable:

- owner;
- preconditions;
- authority;
- inputs and their identities;
- selected executor/surface;
- expected outputs;
- validation;
- durable output identity;
- failure/stop condition;
- next stage or return route.

A stage may be read-only, mutating, runtime-executing, validating, or waiting on
an external gate.

## 2.4 Task execution

A **task execution** is one concrete run of a workflow or one bounded task that
may span stages, sessions, repositories, executors, surfaces, and human gates.

Its live durable state belongs in a task capsule or successor mechanism.

## 2.5 Reasoning executor

A **reasoning executor** is the actor selecting or reasoning about actions.

Examples:

- ChatGPT;
- Codex;
- a human operator.

Reasoning executor identity is descriptive. It MUST NOT become the task's
semantic identity.

## 2.6 Operation surface

An **operation surface** is the mechanism through which a concrete operation is
performed.

Examples:

- GitHub connected tools;
- local shell;
- browser upload;
- Gmail read;
- JFLAP;
- a project runtime;
- a compiler;
- a future connector.

Operation surfaces have capability boundaries independent of the reasoning
executor using them.

## 2.7 Execution topology

An **execution topology** describes where required state lives and which surfaces
must cooperate.

Initial topology classes are conceptual, not yet a frozen schema:

- remote-only;
- local-only;
- local -> remote ingress;
- remote -> local execution;
- mixed/composed.

Topology determines which state identities must be checked before continuation.

## 2.8 Checkpoint

A **checkpoint** is a durable identity from which the next safe action can be
recovered.

Examples:

- Git commit/ref;
- validated remote commit;
- runtime result manifest;
- saved artifact hash;
- persisted workflow stage record.

A checkpoint is not synonymous with "Git commit" when required runtime state
exists outside Git.

## 2.9 Artifact class

An **artifact class** describes the lifecycle and Git expectations of a project
artifact without moving project-specific artifact semantics into workspace-control.

Candidate common classes:

- `SOURCE`;
- `INPUT_EXTERNAL`;
- `GENERATED_TRACKED`;
- `GENERATED_LOCAL`;
- `RUNTIME_STATE`;
- `DELIVERY_ARTIFACT`;
- `TRANSIENT`.

Projects MAY map or extend these concepts.

workspace-control should understand lifecycle expectations, not scientific
meaning.

## 2.10 Validation barrier

A **validation barrier** is the evidence boundary that must pass before a
dependent stage may rely on a result.

Validation may include:

- structural/static checks;
- expected changed-path set;
- commit/ref equality;
- hashes;
- semantic invariants;
- unit/numerical tests;
- build output;
- artifact freshness;
- visual inspection;
- human judgment where the owning workflow requires it.

Process exit alone is not automatically sufficient.

## 2.11 Suspension

A **suspension** is a safe non-failure stop because continuation requires an
external capability or authority.

Examples:

- browser ingress;
- JFLAP execution;
- unavailable local runtime;
- required human visual judgment;
- explicit user decision.

A suspension records the first incomplete stage and the required resume
condition.

## 2.12 Failure

A **failure** means a stage did not establish its required result or validation.

After a failed or ambiguous mutation:

```text
inspect actual durable state
-> determine what completed
-> continue from first safe incomplete stage
```

Blind retry is forbidden.

## 2.13 Resumability

A task is **resumable** when another control cycle can recover:

- parent task/owner;
- workflow identity when applicable;
- completed stages;
- validation already established;
- last durable checkpoint;
- unresolved gate/failure;
- first safe incomplete stage;
- expected return route.

Completed validated stages SHOULD NOT be replayed merely because the
conversation, executor, or user turn changed.

## 2.14 HANDOFF_SAFE

A task is **HANDOFF_SAFE** when a receiving executor can recover the next safe
action entirely from durable authority and evidence relevant to the topology
actually used.

v2 MUST NOT require local checkout state for a remote-only task solely because
the v1 checker did.

Topology-specific handoff evidence may include:

### Remote-only

- logical repository identity;
- branch/ref;
- exact remote checkpoint;
- mutation scope;
- completed validation;
- remaining work;
- next safe action.

### Local

- logical repository identity;
- exact checkout/worktree;
- branch;
- HEAD;
- dirty/staged state;
- runtime/environment identity when required;
- remaining work;
- next safe action.

### Composed/hybrid

- durable remote checkpoint;
- required local/runtime identities;
- synchronization boundary;
- which side is authoritative for each remaining stage.

HANDOFF_SAFE is a property of recoverability, not of a specific executor.

## 2.15 Executor/surface selection

Selection SHOULD answer:

> For this operation class, authority, consequence level, data locality/topology,
> and known capability evidence, what is the least cumbersome verified capable
> surface/executor combination?

Selection MUST NOT hard-code current tool limitations as timeless architecture.

A known deterministic project procedure SHOULD be preferred over repeatedly
reinventing the same shell/tool sequence.

---

# 3. Continuous routing and return routing

Routing is not a startup-only activity.

When task ownership materially changes, the controller must reroute before
acting.

Examples:

```text
tutoring -> persistence
persistence -> report
report -> runtime build
analysis -> experiment
experiment -> interpretation
source edit -> artifact validation
```

Return routing is equally important:

```text
parent owner
-> subordinate stage/workflow
-> validation/checkpoint
-> return to parent owner
```

An explicit owner stack is not required by this draft. It should be introduced
only if real workflows demonstrate that implicit return state is insufficient.

---

# 4. Human and external-tool gates

Human involvement MUST NOT be collapsed into one generic approval mechanism.

Initial distinctions:

## 4.1 Mechanical capability bridge

The human performs a bounded mechanical operation because the active surface
cannot.

Example:

```text
existing local bytes
-> browser upload
-> durable remote Git
-> DIRECT_TOOL verification
```

The human is not thereby the new reasoning executor for the whole task.

## 4.2 Specialized external-tool execution

A specialized tool must genuinely be operated outside the available autonomous
surface.

Example:

- user constructs/tests an automaton in JFLAP.

The workflow should suspend, checkpoint completed work, then resume from the
first incomplete stage when the returned artifact/evidence exists.

## 4.3 Substantive human judgment

A human decision is itself authoritative evidence.

Examples:

- final visual acceptance;
- ambiguous instructor intent;
- scientific interpretation requiring user ownership;
- external submission approval.

This gate cannot be silently replaced by mechanical automation.

---

# 5. Workflow descriptors versus task capsules

These are deliberately separate.

## 5.1 Workflow descriptor

Stable project-owned procedure:

```text
how this kind of task works
```

It SHOULD be reusable across executions.

## 5.2 Task capsule

Live durable execution state:

```text
where this particular task is now
```

It SHOULD refer to project-owned workflow/context rather than duplicate it.

A future capsule v2 may record:

- workflow identity;
- parent task;
- completed stage IDs;
- current/suspended stage;
- remote checkpoints;
- local/runtime checkpoints;
- validations;
- artifact identities;
- blockers/gates;
- remaining work;
- next safe action.

---

# 6. Project-owned deterministic entrypoints

When a multi-step local/runtime sequence becomes stable and reusable, the owning
project SHOULD prefer a tracked named procedure over repeated reconstructed shell
blocks.

Examples:

- presentation finalize/build;
- experiment launch;
- report build;
- dataset validation;
- artifact packaging.

The project procedure owns its internal commands and project semantics.

workspace-control may route to it, establish prerequisites, and validate generic
execution state.

"One local command" is an optimization, not a universal requirement. Long,
expensive, or failure-sensitive workflows may deliberately expose multiple
checkpointed commands/stages.

---

# 7. Worktree preparation

v2 SHOULD add a deterministic, non-destructive worktree preparation primitive.

Conceptual request:

```text
repository
branch/ref
durable target path
expected remote checkpoint
intent
```

Conceptual results:

- `READY`;
- `NEEDS_REVIEW`;
- `BLOCKED_DIRTY`;
- `BLOCKED_DIVERGED`;
- `BLOCKED_IDENTITY`;
- other explicit non-destructive outcomes.

It MUST NOT silently:

- clean;
- reset;
- stash;
- force checkout;
- switch unrelated checkouts;
- overwrite unrelated work.

Creating an isolated missing worktree may be allowed when explicitly authorized.

---

# 8. Remote-aware preflight

v1 preflight is local-checkout centered.

v2 SHOULD preserve that strong local inspection while adding topology-aware
preflight.

## 8.1 Remote-only preflight

Possible checks:

- logical repository identity;
- expected remote;
- expected branch/ref;
- advertised SHA;
- write policy;
- allowed mutation scope;
- expected parent when mutation is ref-dependent.

No local checkout should be manufactured merely to satisfy this mode.

## 8.2 Local preflight

Preserve and extend v1 checks:

- checkout identity;
- branch;
- HEAD;
- staged/unstaged/untracked state;
- origin;
- remote relation;
- runtime/environment requirements.

## 8.3 Composed preflight

When remote and local stages cooperate:

- establish both identities;
- establish which checkpoint must be synchronized;
- establish the transition rule;
- prohibit assumptions that remote mutation moved the local checkout.

---

# 9. Artifact lifecycle and Git policy

Projects SHOULD be able to declare lifecycle expectations for relevant outputs.

The declaration may answer:

- Is this authoritative source?
- Is it external input?
- Is it generated deterministically?
- Should it be committed?
- Is it local/runtime-only?
- Is it a delivery/export artifact?
- Is it transient?

This enables more reliable:

- `git status` interpretation;
- changed-path validation;
- artifact freshness checks;
- cleanup decisions;
- handoff state.

workspace-control SHOULD NOT decide whether a scientific artifact is correct.

---

# 10. Cross-authority consistency validation

Projects MAY provide validators that detect contradictions among routed
authorities.

Examples:

- stale asset revision references;
- stale pending/completed status;
- mismatched source filenames;
- report references to missing generated artifacts;
- manifest/source hash disagreements.

workspace-control SHOULD define how validators participate in stage validation,
but project repositories own their semantics.

---

# 11. Capability evidence

v2 requires enough capability knowledge to avoid selecting unverified surfaces,
but this draft does NOT introduce a large global capability database.

Initial policy:

- capability claims are operation-class specific;
- successful evidence from one operation MUST NOT imply universal executor trust;
- repeated evidence across independent projects increases confidence;
- known hard capability boundaries should be preserved;
- runtime capability can change over time and should not be encoded as permanent
  truth when it can be inspected.

A future minimal representation may emerge after implementation experience.

---

# 12. Concurrency and ordering

Initial orchestration invariant:

- independent read-only operations MAY run concurrently when useful;
- state-dependent mutations MUST be serialized in dependency order;
- a dependent stage MUST NOT consume an unvalidated predecessor result.

This is sufficient until real workflows demonstrate a stronger requirement.

---

# 13. Failure, ambiguity, and idempotency

A workflow SHOULD make repeated execution safe where practical.

Useful behavior includes:

- detect already-ingested source identity;
- verify and no-op when durable state is already correct;
- detect existing artifact/checkpoint;
- distinguish "operation failed" from "operation may have applied but response
  failed";
- inspect state before retry.

A verified no-op is a successful workflow outcome.

---

# 14. Durable state versus generated status

Stable architecture and policy SHOULD remain mostly timeless.

Volatile state SHOULD live in:

- task capsules;
- Git refs/checkpoints;
- manifests;
- result records;
- runtime evidence;
- generated status views.

Human-readable status summaries MAY exist, but they must be clearly derived and
must not become competing authority.

---

# 15. Initial v2 implementation boundary

This architecture draft deliberately does not yet choose final schemas or command
names.

The first implementation phase after review should decide the smallest changes
needed to integrate:

- the provisional shared operator/tutor bridge;
- the proven Codex thin-adapter layer;
- topology-aware preflight;
- topology-aware handoff;
- task capsule v2 stage/resume semantics;
- safe worktree preparation;
- minimal workflow descriptor contract;
- artifact lifecycle declarations;
- validation integration.

PADataset, MTH602, EAS501, CIS560, and the preserved Phase-4 evidence branches
remain untouched during this architecture phase.

---

# 16. Required regression evidence before promotion

v2 should not be promoted to `main` merely because schemas validate.

At minimum, validate:

1. remote-only DIRECT_TOOL mutation and reread;
2. DIRECT_TOOL -> local runtime -> DIRECT_TOOL composition;
3. mechanical browser ingress -> DIRECT_TOOL recovery;
4. human judgment suspension -> resume;
5. safe worktree creation/preparation;
6. dirty/diverged worktree refusal;
7. verified no-op/idempotent re-entry;
8. ambiguous mutation -> state inspection before retry;
9. ChatGPT -> Codex handoff;
10. Codex -> ChatGPT handoff;
11. remote-only HANDOFF_SAFE;
12. local-runtime HANDOFF_SAFE;
13. workflow resume from first incomplete stage;
14. project-owned validation failure preventing dependent continuation.

A real project workflow should be used for at least one regression after the
control-plane mechanics pass. PADataset migration remains a later explicit
decision.

---

# 17. Non-goals

v2 is not intended to become:

- a super-repository;
- a scientific knowledge base;
- a course-content database;
- a distributed scheduler;
- a general DAG engine;
- a replacement for Git;
- a replacement for project-owned scripts;
- a mandatory external agent framework;
- a giant permanent executor-capability registry;
- a reason to route every operation through one tool.

The system should remain understandable and operable with ordinary Git,
repository context, deterministic scripts, ChatGPT/direct tools, a human
terminal, and Codex.

---

# 18. Review questions

Before broader implementation, review this draft against the evidence and answer:

1. Does any shared concept still accidentally absorb project-domain authority?
2. Are workflow descriptors and task capsules separated cleanly enough?
3. Are reasoning executor, operation surface, and topology distinct enough?
4. Is HANDOFF_SAFE defined by actual recoverability rather than v1 local-state
   assumptions?
5. Are suspension, failure, and human judgment distinguished clearly?
6. Is artifact lifecycle generic enough to help orchestration without encoding
   project semantics?
7. Is the proposed stage contract sufficient for multi-tool autonomous control
   cycles?
8. Are worktree preparation and preflight non-destructive by construction?
9. Does the architecture support known deterministic procedures without forcing
   every task into a formal workflow?
10. Is the implementation boundary still small enough to avoid building an
    unnecessary workflow engine?
