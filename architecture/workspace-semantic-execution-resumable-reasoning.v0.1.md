# Resumable Reasoning Process v0.1

Status: **DESIGN / BENCHMARK CANDIDATE**

Parent task:
`workspace-semantic-execution-migration-v1`

Benchmark contract:
`benchmarks/workspace-semantic-execution/resumable_reasoning_v1.json`

## 1. Purpose

Define the smallest durable abstraction required for a reasoning model such as ChatGPT Instant to participate in long-horizon Workspace Control work without relying on a long-lived conversation.

The core idea is:

> The durable reasoning process is the continuity boundary. A model invocation is a disposable executor of one bounded reasoning quantum.

This is not an assumption that repeated Instant calls become equivalent to stronger reasoning. The benchmark contract explicitly separates task horizon/size from intrinsic difficulty.

---

## 2. Process model

```text
ReasoningProcess
    │
    ├─ objective
    ├─ durable semantic state
    ├─ evidence references
    ├─ inherited constraints
    ├─ authority references
    ├─ reasoning requirement
    ├─ child processes
    ├─ generation / ownership
    └─ continuation condition
             │
             ▼
       model invocation
             │
     ┌───────┼──────────┐
     ▼       ▼          ▼
  result   child work   wait
     │       │          │
     └───────┼──────────┘
             ▼
       durable checkpoint
             │
             ▼
   invocation terminates
```

A later compatible executor may resume from the durable checkpoint.

The later executor need not be:

- the same chat;
- the same worker identity;
- the same model;
- the same provider;

unless the task contract explicitly requires one of those properties.

---

## 3. State model

Minimum durable fields:

```text
process_id
objective
generation
status
invocation_count

reasoning_requirement
context_query

established_findings
open_hypotheses
unresolved_questions
evidence_refs

candidate_actions
child_processes

invariants
constraints
authority_refs
validation_requirements

last_executor
last_checkpoint
next_safe_action
```

### Status

```text
READY
RUNNING
WAITING_EXTERNAL
READY_TO_RESUME
DECOMPOSED
ESCALATION_REQUIRED
AUTHORITY_BLOCKED
COMPLETED
FAILED
SUPERSEDED
```

These statuses describe reasoning-process state. They do not themselves grant execution authority.

---

## 4. Why this is different from "keep saying continue"

A naive continuation loop is:

```text
chat context
→ continue
→ continue
→ continue
```

The proposed model is:

```text
durable state
→ invocation
→ verified checkpoint
→ invocation ends

event / scheduler
→ recover durable state
→ new invocation
→ verified checkpoint
```

The second model permits:

- worker replacement;
- stale-worker rejection;
- asynchronous waits;
- context compaction;
- model/provider substitution;
- independent critique;
- branching/decomposition;
- exact provenance;
- replay/inspection.

Conversation history becomes optional supporting evidence rather than authoritative process state.

---

## 5. Reasoning quantum

One invocation should have a bounded contract.

A worker may:

- inspect the current bounded semantic state;
- retrieve additional evidence permitted by the task;
- reason about one decision/node;
- propose candidate actions;
- implement/execute an already-authorized bounded action when its executor surface permits;
- interpret a completed external result;
- decompose an oversized node;
- identify a genuine escalation requirement;
- checkpoint durable state.

A worker should not:

- consume arbitrary historical context merely because it exists;
- repeatedly poll an unchanged external wait;
- widen authority;
- keep working on a node after its bounded envelope is exceeded;
- repeatedly retry an intrinsically hard node merely to avoid escalation.

---

## 6. Size versus difficulty

This distinction is foundational.

### TOO_LARGE

The task is intellectually manageable but its current node has too much context, too many independent actions, or too broad a change surface.

Response:

```text
DECOMPOSE
→ create smaller child nodes
→ inherit constraints/authority
→ route children independently
```

Examples:

- inspect six independent subsystems;
- modify ten independent files;
- compare many experiment outputs;
- review a long paper across independent sections.

### INTRINSICALLY_DIFFICULT

Reasonable decomposition has already reduced the task, but the remaining decision still requires stronger integrated reasoning.

Response:

```text
ESCALATION_REQUIRED
→ persist lower-tier evidence
→ state exact unresolved decision
→ route to stronger reasoning tier
```

Examples may include:

- subtle causal discrimination across conflicting evidence;
- novel architecture decision with coupled invariants;
- difficult proof/math residual;
- final synthesis where weaker models repeatedly fail objective review.

The router should not infer difficulty merely from importance.

---

## 7. Async wait semantics

External waiting is not reasoning.

```text
request CI / experiment / render / external action
        ↓
persist WAITING_EXTERNAL
        ↓
terminate model invocation
        ↓
deterministic event observer
        ↓
result becomes durable
        ↓
state → READY_TO_RESUME
        ↓
invoke reasoning executor
```

No model invocation should exist solely to ask:

> Is it done yet?

The current GitHub/GitRunner model already provides an existence proof for this pattern.

---

## 8. Ownership and generation

Recent Instant worker benchmarks established that durable ownership cannot depend on conversational self-identification.

Required principles:

- unique worker/session identity comes from a durable atomic claim;
- existing identity refs are collisions, never adoptable identities;
- action ownership is atomic;
- recovery advances generation;
- only current-generation owner may complete;
- stale worker state is rejected even if its local work was previously valid.

For a single resumable reasoning process, generation primarily protects recovery/reassignment.

For parallel decomposition, worker identity and action claims should remain distributed rather than requiring one mutable hot queue.

---

## 9. Context packet

The resumed model should normally receive a small, semantically selected packet.

Example:

```text
PROCESS
  R183

OBJECTIVE
  explain contradiction between experiment E12 and E17

CURRENT FINDINGS
  F31 ...
  F44 ...

LIVE HYPOTHESES
  H2 ...
  H5 ...

INVARIANTS
  I7 ...

RELEVANT EVIDENCE
  E12/result
  E17/result
  config-diff D4

AUTHORITY
  analysis only; no live trigger authority

VALIDATOR
  identify discriminating experiment and preserve X/Y constraints

NEXT
  compare changed conditions; decompose if > bounded envelope
```

Raw evidence should remain retrievable by reference.

A frontier model should not receive a giant conversation transcript merely because a long task existed.

---

## 10. Independent critique

Fresh resumptions permit a useful pattern unavailable in one monolithic conversation:

```text
Worker A
→ candidate interpretation/design

Worker B
→ independent adversarial review

Worker C
→ reconciliation/synthesis

deterministic/domain validator
→ accept/reject
```

The independent critic should not automatically receive A's hidden reasoning. It receives the candidate artifact, authoritative evidence, requirements, and review contract.

This may reduce anchoring and compensate for some weaker-model behavior, but it remains an empirical hypothesis.

---

## 11. Model substitution

A reasoning process declares requirements rather than a hard-coded model.

Example:

```text
ReasoningRequirement
  class: MODERATE
  required_capabilities:
    - github-read
    - code-reasoning
    - experiment-interpretation
  context_max: bounded
  privacy: remote-allowed
```

The router may select Instant.

If the node later becomes:

```text
ReasoningRequirement
  class: HIGH
  residual_reason:
    conflicting causal evidence after decomposition
```

the same process can be resumed by a stronger executor.

The process identity and provenance remain stable across executor changes.

---

## 12. Validation

A model does not declare itself complete.

A `COMPLETED` process must reference:

- domain/objective validator;
- output artifact/result identity;
- supporting evidence;
- provenance;
- any required independent review.

For research:

```text
model interpretation
≠
scientific verdict
```

For tutoring:

```text
model-produced correct solution
≠
student mastery
```

For documents:

```text
build exit 0
≠
artifact QA pass
```

The generic process model must preserve those domain-specific distinctions.

---

## 13. Benchmark interpretation

A successful stateless-resume run proves:

- durable state is sufficient for continuation;
- the worker can recover context;
- long horizon does not require one conversation.

It does **not** prove:

- Instant has frontier-level reasoning;
- every task should use Instant;
- more invocations compensate for intrinsic difficulty.

The production decision should be based on repeated representative benchmark cases.

---

## 14. Production hypothesis

If the benchmark succeeds, the production pattern becomes:

```text
Program / Workflow
       ↓
ReasoningProcess nodes
       ↓
deterministic eligibility + authority
       ↓
router
       ↓
Instant / local / frontier / human
       ↓
bounded reasoning quantum
       ↓
durable result
       ↺
```

This makes frontier reasoning a sparse high-value resource rather than the persistence mechanism for the whole workflow.
