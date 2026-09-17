# Executor Portability Contract

Status: **provisional v0.1**

This contract defines the cross-project requirements that allow work to move
between an agentic executor and ChatGPT-assisted human execution without
redesigning the workflow.

Normative terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY**
are intentional.

## 1. Definition

A workflow has **executor portability** when Codex and ChatGPT-assisted human
execution can independently recover the next correct and safe action from
durable repository and runtime evidence without requiring the previous
executor's private conversation state.

Changing executors should change the degree of automation, not the canonical
workflow.

## 2. Durable knowledge

Essential operational, scientific, course, artifact, or provenance knowledge
MUST NOT exist only in:

- an agent conversation;
- a ChatGPT conversation;
- a Codex Skill;
- `AGENTS.md`;
- an MCP result;
- an automation definition;
- an executor-private scratchpad.

Durable knowledge MUST live in the owning repository context, authoritative
source/evidence, tracked procedure, tracked configuration, validated artifact,
or another explicitly durable authority.

## 3. Executor-neutral core

Canonical context and reusable procedures MUST remain operable without Codex.

Agent-specific instructions MAY improve discovery, automation, or efficiency,
but removing the entire agent-adapter layer MUST NOT make an established
workflow conceptually inoperable.

If an essential procedure exists only inside an agent Skill, that is an
executor-portability defect.

## 4. Agent adapters

`AGENTS.md`, Skills, MCP configuration, automation definitions, and similar
agent-specific mechanisms MUST act as adapters to canonical knowledge and
procedures.

They MUST NOT silently become competing sources of scientific, course, or
artifact truth.

Where practical, an agent adapter SHOULD point to an executor-neutral tracked
procedure or implementation rather than duplicate it.

## 5. Repository identity and checkout state

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

Volatile observations MUST be obtained from the actual checkout when needed and
SHOULD NOT be stored as timeless registry truth. Examples include:

- current branch;
- current HEAD;
- dirty state;
- staged state;
- ahead/behind counts;
- worktree list;
- running processes;
- current GPU/hardware state.

## 6. Mutation preflight

Before mutation, an executor MUST establish the relevant:

- repository identity;
- checkout/worktree path;
- branch;
- HEAD;
- dirty/staged state;
- intended mutation scope;
- required runtime or external state.

An executor MUST NOT infer checkout identity from an already-open GUI,
notebook browser, remembered path, or prior conversation.

## 7. Dirty-work protection

Executors MUST NOT automatically:

- clean;
- reset;
- stash;
- switch branches;
- overwrite;
- delete;
- broadly stage unrelated work

merely to make a checkout match an expected branch or documentation state.

Isolated worktrees SHOULD be preferred for bounded task branches when the
primary checkout contains unrelated work.

`git add .` or equivalent broad staging SHOULD NOT be used in a dirty research
or coursework checkout.

## 8. Execution evidence

A proposed, inspected, generated, or explained command MUST NOT be represented
as having executed.

Runtime claims MUST be grounded in returned execution evidence such as:

- stdout/stderr;
- logs;
- process state;
- generated files;
- metadata;
- checkpoints;
- result summaries;
- validated external state.

Executor recollection is not runtime evidence.

## 9. Artifact completion

Process exit status alone MUST NOT establish successful completion.

Each reusable workflow SHOULD define an artifact or state contract identifying:

- expected outputs;
- required metadata/provenance;
- semantic correctness conditions;
- structural/static checks;
- runtime/scientific checks where applicable;
- failure indicators.

Completion MUST be judged against that contract.

## 10. Git and synchronization

For tracked source, Git/GitHub is the synchronization mechanism between
executors.

Tracked changes SHOULD follow:

```text
inspect
→ bounded change
→ execute when needed
→ validate artifact/result
→ targeted diff
→ narrow staging
→ commit
→ push
→ reread pushed state
```

An executor SHOULD prefer pushed validated checkpoints before another executor
takes over.

## 11. Handoff-safe state

A task is **HANDOFF-SAFE** when another executor can determine, from durable
evidence:

- repository identity;
- checkout/worktree and branch;
- relevant HEAD or last pushed checkpoint;
- task goal;
- acceptance criteria;
- constraints;
- important decisions already made;
- operations actually executed;
- artifacts produced;
- validation completed;
- unresolved failures/blockers;
- remaining work;
- next safe action.

A clean commit is useful but does not by itself guarantee a handoff-safe state.
Unrecorded runtime work may still make a task nonportable.

## 12. Long-running tasks

A task expected to span sessions, executors, significant runtime, or substantial
agent quota SHOULD maintain a durable task/execution record.

That record MAY contain:

- task ID;
- repository/repositories;
- base SHA;
- task branch/worktree;
- status;
- acceptance criteria;
- allowed mutation scope;
- decisions;
- executed operations;
- artifacts;
- validation;
- blockers;
- next safe action.

The executor named in such a record is descriptive only and MUST NOT become part
of the task's semantic identity.

## 13. Agent quota or availability failure

Loss of Codex availability, exhaustion of agent quota, or intentional choice not
to use an agent MUST reduce automation only.

It MUST NOT require:

- rewriting canonical context;
- converting the task into another workflow format;
- recreating hidden agent knowledge manually;
- abandoning an established procedure.

ChatGPT-assisted human execution SHOULD be able to continue from the same
durable state.

## 14. Runtime-only state

Ignored/local datasets, caches, checkpoints, hardware state, environment state,
and other runtime-only resources MAY remain outside Git.

When required to continue a task, their identity MUST be recoverable through
explicit paths, manifests, metadata, hashes, logs, task records, or targeted
inspection.

Absence from Git MUST NOT be interpreted automatically as absence from the
prepared machine.

## 15. Cross-repository work

Cross-repository tasks MUST preserve each repository's independent authority and
Git history.

A coordinator MAY reference exact repository SHAs and roles, but MUST NOT
silently move scientific/course authority into the control plane.

Each writable repository SHOULD use its own branch/worktree for its own
mutations.

The workspace control plane coordinates; it does not become a super-repository.

## 16. Read-only and externally owned repositories

A repository marked non-writable in the workspace registry MUST be treated as
read-only unless the user explicitly changes that policy.

Dirty external/upstream repositories MUST NOT be cleaned or normalized merely
for agent convenience.

Broad recursive operations are forbidden when a registered repository contains
or overlaps another project checkout.

## 17. Completion authority

When claims conflict, prefer:

```text
owning authoritative context/evidence
        +
validated artifact/runtime evidence
        +
actual Git state
```

over either executor's conversational recollection.

A generated status index or agent summary is an observation aid, not authority.

## 18. Portability test

An important workflow SHOULD eventually pass both directions:

```text
Codex → ChatGPT-assisted human execution
ChatGPT-assisted human execution → Codex
```

The receiving executor should be given only the normal repository/control-plane
entry route and durable task state.

If a special explanatory handoff must be invented because essential state existed
only in the prior conversation, the workflow has failed executor portability.

## 19. Current boundary

This v0.1 defines architecture only.

It does not yet establish:

- Codex installation;
- Codex sandbox configuration;
- global or repository `AGENTS.md`;
- Skills;
- MCP integrations;
- automations;
- an execution-plan schema;
- runtime reproduction of any project workflow.

Those should be added only after this executor-neutral contract is reviewed and
committed.
