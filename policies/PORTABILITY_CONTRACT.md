# Executor Portability Contract

Status: **v2 candidate**

Normative terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY**
are intentional.

## 1. Definition

A workflow has **executor portability** when a suitable receiving executor can
recover the next correct and safe action from durable project/control-plane
authority and evidence without requiring the previous executor's private
conversation state.

Changing executors or operation surfaces may change the degree of automation,
but it must not redefine project authority, validation standards, or the
canonical workflow.

## 2. Durable knowledge

Essential operational, scientific, course, artifact, provenance, workflow, or
resume knowledge MUST NOT exist only in:

- an agent conversation;
- a ChatGPT conversation;
- a Codex Skill;
- `AGENTS.md`;
- an MCP/connector result;
- an automation definition;
- an executor-private scratchpad.

Durable knowledge MUST live in the owning repository context, tracked workflow or
procedure, task capsule, authoritative source/evidence, validated artifact,
runtime record, or another explicitly durable authority.

## 3. Authority boundary

workspace-control coordinates reusable execution semantics.

It MUST NOT silently absorb project-domain truth.

Project repositories retain authority for their own:

- scientific/course truth;
- implementation truth;
- source provenance;
- artifact semantics;
- project workflows;
- project-specific validation.

Authority is typed. One source may own one fact class without globally outranking
all other sources.

## 4. Reasoning executor, operation surface, and topology

These concepts are distinct.

A **reasoning executor** selects or reasons about actions, for example ChatGPT,
Codex, or a human.

An **operation surface** performs a concrete operation, for example GitHub
connected tools, a terminal, browser ingress, Gmail read, JFLAP, a compiler, or a
project runtime.

An **execution topology** describes where required state lives and how surfaces
must cooperate, for example remote-only, local, local-to-remote ingress, or
composed execution.

Capability on one surface MUST NOT be generalized into universal executor trust.

## 5. Executor-neutral core and thin adapters

Canonical context and reusable procedures MUST remain operable without any one
executor-specific adapter.

`AGENTS.md`, Skills, connector routing, automations, and similar mechanisms MAY
improve discovery or automation, but MUST NOT become competing sources of
project truth, workflow semantics, task execution evidence, or artifact
completion state.

Removing an adapter may reduce automation. It MUST NOT make an established
workflow conceptually unrecoverable.

## 6. Workflow and shared-contract version binding

When a task depends on a reusable workflow or shared contract, the dependency
SHOULD be bound to an exact durable identity such as repository + path + Git
checkpoint/content identity.

A long-running task MUST NOT silently resume against a materially changed
workflow definition.

Migration to a newer workflow/contract version is an explicit, validated state
transition.

## 7. Repository identity and current state

A logical Git repository MUST be distinguished from any individual checkout or
worktree.

Stable registry information MAY include:

- logical repository name;
- canonical path;
- remote;
- role;
- authority;
- mutability policy;
- canonical branch;
- context entry point.

Volatile observations MUST be obtained from the relevant current surface when
needed and SHOULD NOT be stored as timeless registry truth.

Examples include:

- current branch/ref;
- HEAD/advertised SHA;
- dirty/staged state;
- ahead/behind counts;
- worktree list;
- running processes;
- hardware/runtime availability.

## 8. Topology-aware preflight

Before mutation, an executor MUST establish the state relevant to the topology
actually used.

### Remote-only

Establish, as applicable:

- logical repository identity;
- expected remote;
- branch/ref;
- advertised SHA;
- expected parent;
- mutation policy/scope;
- required connector/write capability.

Do not manufacture a local checkout merely to satisfy preflight.

### Local

Establish, as applicable:

- checkout/worktree identity;
- branch;
- HEAD;
- dirty/staged/untracked state;
- origin/remote relation;
- required runtime/environment.

### Composed

Establish both sides needed for the transition and the exact synchronization
boundary.

Remote mutation MUST NOT be assumed to have moved a local checkout.

## 9. Dirty-work protection

Executors MUST NOT automatically:

- clean;
- reset;
- stash;
- switch branches;
- force checkout;
- overwrite;
- delete;
- broadly stage unrelated work

merely to normalize a checkout.

Isolated worktrees SHOULD be preferred for bounded task branches when unrelated
work exists.

## 10. Execution evidence

A proposed, inspected, generated, or explained operation MUST NOT be represented
as having executed.

Claims about execution SHOULD use the strongest available evidence, including:

- stdout/stderr;
- exit status;
- Git refs/SHAs;
- changed-path sets;
- hashes;
- logs;
- runtime state;
- generated files;
- result records;
- artifact identities.

An executor's recollection is not execution evidence.

## 11. Artifact completion and validation barriers

Process exit status alone MUST NOT establish successful completion.

Each material stage SHOULD define the evidence required before a dependent stage
may consume its result.

Validation may include:

- structural/static checks;
- exact changed-path checks;
- commit/ref equality;
- hashes;
- semantic invariants;
- unit/numerical tests;
- artifact freshness;
- visual inspection;
- human judgment required by the owning workflow.

Project repositories own semantic correctness.

## 12. Checkpoints and resumability

A checkpoint may be one durable identity or a coherent bundle of identities.

A resumable task allows another control cycle to recover:

- parent task/execution owner;
- workflow identity/version when applicable;
- completed validated stages;
- last required checkpoint/bundle;
- unresolved gate/failure;
- first safe incomplete stage;
- next/return route.

Completed validated stages SHOULD NOT be replayed merely because the user turn,
conversation, executor, or surface changed.

## 13. HANDOFF_SAFE and EXECUTION_READY

A task is **HANDOFF_SAFE** when durable authority/evidence is sufficient for a
suitable receiver to recover the next safe action for the topology actually
used.

A task may be HANDOFF_SAFE even when a particular proposed receiver is not
**EXECUTION_READY** because it lacks a connector, credentialed connection,
runtime, hardware resource, required artifact, or human decision.

Conversely, technical ability to act does not make incomplete task state
HANDOFF_SAFE.

Remote-only tasks MUST NOT require local checkout state solely because an older
checker did.

## 14. Human/external-tool gates

Human involvement MUST distinguish at least:

- mechanical capability bridge;
- specialized external-tool execution;
- substantive human judgment.

A required human gate for one stage does not revoke standing authority for other
bounded reversible stages.

## 15. Capability, access, authority, and consequence

Technical capability and access permission do not themselves authorize an
operation.

Selection must consider:

- operation class;
- capability evidence;
- data locality/topology;
- bounded task/project authority;
- consequence level.

Externally consequential or destructive actions MAY require stronger authority
or explicit human judgment even when technically easy.

Secrets, credentials, tokens, private keys, and equivalent authentication
material MUST NOT be persisted in ordinary Git workflow/task state.

## 16. Failure, ambiguity, and idempotency

After a failed or ambiguous mutation:

```text
inspect actual durable state
-> determine what completed
-> continue from first safe incomplete stage
```

Blind retry is forbidden.

A verified no-op is a valid successful workflow result when state is already
correct.

## 17. Long-running tasks

Work spanning sessions, executors, substantial runtime, multiple repositories,
or real human/tool gates SHOULD maintain durable task state.

That state coordinates work. It does not become project-domain authority.

Detailed event history MAY live in referenced logs/records while the task
capsule remains a concise recoverable snapshot.

## 18. Runtime-only state

Ignored/local datasets, caches, checkpoints, hardware state, and environment
state MAY remain outside Git.

When required to continue, their identity must be recoverable through explicit
paths, manifests, hashes, logs, task records, or targeted inspection.

Absence from Git MUST NOT automatically be interpreted as absence from the
prepared machine.

## 19. Cross-repository work

Cross-repository tasks MUST preserve each repository's independent authority and
Git history.

The control plane coordinates. It does not become a super-repository.

Each writable repository SHOULD use its own safe mutation boundary.

## 20. Availability or quota failure

Loss of Codex availability, connector availability, agent quota, or intentional
choice not to use an executor SHOULD reduce automation only.

It MUST NOT require redesigning the canonical workflow or recreating hidden
executor knowledge manually.

## 21. Completion authority

When claims conflict, prefer:

```text
owning authoritative context/evidence
        +
validated artifact/runtime evidence
        +
actual durable state
```

over conversational recollection.

Generated status or handoff views are convenience projections, not authority.

## 22. Portability tests

Important workflows SHOULD eventually demonstrate relevant directions such as:

- ChatGPT DIRECT_TOOL -> Codex;
- Codex -> ChatGPT DIRECT_TOOL;
- ChatGPT/direct tools -> human terminal/runtime -> ChatGPT;
- human/external-tool suspension -> resume;
- remote-only handoff;
- local-runtime handoff.

The receiving executor should need the normal entry route, durable task state,
and referenced owning context/evidence rather than a special prose reconstruction.

## 23. Boundary

This contract defines portable semantics, not a mandatory orchestration
framework.

workspace-control should remain understandable and operable with ordinary Git,
repository context, deterministic scripts, ChatGPT/direct tools, human-operated
surfaces, and Codex.
