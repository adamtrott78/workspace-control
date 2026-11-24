# Workspace Semantic Execution — Cognitive / Execution / State Architecture v0.1

Status: **DESIGN CANDIDATE / EVOLUTIONARY, NOT FROZEN**

Parent task: `workspace-semantic-execution-migration-v1`

Related:
- `architecture/workspace-semantic-execution-recursive-asynchronous-reasoning.v0.1.md`
- `architecture/workspace-semantic-execution-core.v0.1.json`
- `architecture/workspace-semantic-execution-orchestrator-implementation-plan.v0.1.md`

## 1. Reframing

Workspace Semantic Execution is not primarily an "Instant worker scheduler."

It is an **external cognitive + execution system** that combines:

1. **Reasoning process** — recursively decompose, investigate, critique, synthesize, and revise.
2. **Execution process** — translate conclusions into precise authorized effects and verify the real world changed as intended.
3. **State process** — preserve what matters across model turns, workers, failures, waits, and executor generations.
4. **Learning process** — continuously update routing/decomposition policy from validated real-workflow evidence.

No single model invocation owns the process.

## 2. Two coupled loops

### Cognitive loop

```text
LOAD
  ↓
FOCUS
  ↓
REASON
  ↓
PROPOSE / DECOMPOSE / QUESTION
  ↓
OBSERVE / CRITIQUE / VALIDATE
  ↓
CONSOLIDATE
  ↓
CONTINUE / DECOMPOSE / WAIT / REPAIR / ESCALATE / COMPLETE
  ↺
```

Outputs are epistemic or proposed work until separately authorized.

### Execution loop

```text
validated reasoning conclusion
        ↓
CandidateAction
        ↓
Action compilation
        ↓
precondition + authority + capability checks
        ↓
claim / lease / idempotency binding
        ↓
execute exact bounded effect
        ↓
capture receipt / observed state
        ↓
postcondition validator
        ↓
COMMIT / RETRY / REPAIR / COMPENSATE / BLOCK
```

The execution loop is intentionally more deterministic than the reasoning loop.

## 3. Core execution principle

Reasoning should decide **what should happen and why**.

The execution layer should decide **exactly how that proposed conclusion becomes a bounded effect**.

A model-produced conclusion is never executed directly.

Every executable effect must be compiled into an `ActionSpec` containing at least:

- stable action_id;
- parent reasoning/work item;
- exact target/resource;
- action type / executor class;
- immutable input/evidence refs;
- inherited constraints;
- authority refs;
- capability requirements;
- preconditions;
- idempotency key;
- expected effects;
- rollback/compensation contract where meaningful;
- validator/postconditions;
- retry/failure policy;
- provenance/source checkpoint.

## 4. Execution correctness requirements

The executor plane MUST provide:

- **atomic claiming / leases** so two workers do not both own one effect;
- **generation fencing** so stale workers cannot complete after reassignment;
- **idempotency keys** for repeat-safe external actions where supported;
- **precondition checks** immediately before effect;
- **postcondition validation** after effect;
- **effect receipts** recording what actually happened;
- **bounded retries** classified by failure cause;
- **compensation/rollback** where the target system supports it;
- **fail-closed behavior** when authority, target identity, provenance, or state is ambiguous;
- **no execution from semantic inference alone**.

A successful tool call is not automatically a successful action; the postcondition must be observed or otherwise validated.

## 5. State should not use one universal data structure

The system has different state classes with different consistency/query requirements. A single ontology graph, relational database, Git tree, or event log is not optimal for all of them.

Use **polyglot logical structures** while keeping the physical implementation minimal initially.

### 5.1 Append-only event journal — authoritative process history

Best for:
- state transitions;
- claims/leases;
- worker starts/ends;
- wait/wake events;
- action dispatches;
- receipts;
- validation outcomes;
- supersession;
- recovery/reassignment.

Properties:
- immutable ordered events;
- exact timestamps/sequence;
- actor/executor identity;
- source checkpoint;
- correlation IDs;
- replayable.

Purpose:
- audit;
- crash recovery;
- debugging;
- provenance;
- reconstructing materialized state.

This is the durable "what happened" ledger.

### 5.2 Relational materialized state — authoritative current control state

Best for:
- WorkItem current status;
- ReasoningProcess generation/status;
- lease owner/expiry;
- ready queues;
- routing decisions;
- sessions;
- action lifecycle;
- retries;
- validator state;
- resource/quota snapshots.

Properties:
- strong constraints;
- indexes;
- atomic compare-and-swap / transactional updates;
- easy exact queries for READY/BLOCKED/LEASED state.

This is the scheduler's "what is true right now" view.

### 5.3 Task / dependency DAG — work structure

Represent as typed nodes + typed edges:

Nodes:
- WorkItem;
- ReasoningProcess;
- Action;
- Validation;
- Artifact;
- Gate.

Edges:
- decomposes_into;
- depends_on;
- blocks;
- produces;
- validated_by;
- supersedes.

The DAG is optimized for:
- readiness;
- dependency closure;
- recursive decomposition;
- fan-out/fan-in;
- hierarchical synthesis.

Initial physical form can remain relational adjacency tables with recursive queries. A dedicated graph database is not required unless measured workloads justify it.

### 5.4 Semantic ontology / knowledge graph — derived meaning and context projection

Keep the ontology graph, but define its role narrowly.

Best for:
- goals, requirements, constraints;
- claims/findings/questions;
- evidence/support/contradiction;
- semantic similarity/relatedness;
- provenance explanation;
- cross-domain context discovery;
- packet compilation;
- "why did we decide/route this?" queries.

Important:
- rebuildable;
- may contain model-inferred assertions;
- never grants execution authority;
- never becomes the sole source of task/execution state;
- contradiction may remain explicit rather than overwritten.

The graph is a **reasoning/read model**, not the transactional control plane.

### 5.5 Decision records — first-class durable reasoning products

Store each material decision explicitly rather than only as prose.

`DecisionRecord` should include:
- decision_id;
- question / decision boundary;
- alternatives considered;
- evidence refs;
- constraints;
- rejected alternatives + reasons;
- chosen conclusion;
- uncertainty/confidence where meaningful;
- executor/worker identity;
- critic/reviewer refs;
- validator result;
- downstream consequences;
- supersedes/superseded_by.

Decision records are authoritative only for the fact "this decision was recorded"; their execution consequences remain separately authority-gated.

Project them into the semantic graph for retrieval/explanation.

### 5.6 Immutable artifact/evidence store

Best for:
- Git commits;
- files;
- reports;
- experiment outputs;
- logs;
- images;
- rendered artifacts;
- external receipts.

Reference by immutable content hash/version/SHA where possible.

The reasoning state should store references and summaries, not duplicate entire artifacts.

### 5.7 Retrieval indexes — derived acceleration only

Optional:
- full-text index;
- embedding/vector index;
- graph-derived neighborhood cache;
- semantic search index.

These are disposable accelerators.

They may select candidate context but cannot establish truth, authority, or task completion.

### 5.8 Ephemeral session/browser cache

Best for:
- Firefox tab/window mapping;
- active chat surface;
- local focus state;
- clipboard state;
- transient executor health.

Never authoritative.

Loss must be recoverable from durable session/process state.

## 6. Recommended logical architecture

```text
PROJECT-LOCAL AUTHORITATIVE SOURCES
        │
        ├─────────────┐
        │             │
        ▼             ▼
EVENT JOURNAL   RELATIONAL CURRENT STATE
        │             │
        │             ├── work/action/session/lease tables
        │             └── task/dependency DAG tables
        │
        └──────┬──────┘
               ▼
      SEMANTIC PROJECTION
        /      |       \
 claims   provenance   context
    \         |         /
     \        ▼        /
      PACKET / CONTEXT COMPILER
               │
               ▼
       REASONING EXECUTORS
               │
               ▼
        CandidateAction
               │
               ▼
        ACTION COMPILER
               │
        authority/preconditions
               │
               ▼
        EFFECT EXECUTORS
               │
               ▼
       receipts + validators
               │
               └──────────→ EVENT JOURNAL / CURRENT STATE
```

## 7. Why not use the semantic graph for everything?

A graph is excellent when relation traversal and heterogeneous meaning are the primary questions.

It is weaker as the sole store for:
- atomic leases;
- exact queue ownership;
- ordered event replay;
- idempotency enforcement;
- strict transactional state-machine transitions;
- high-confidence "exactly which action is currently claimable?" queries.

Conversely, purely relational control tables are awkward for:
- heterogeneous cross-domain meaning;
- contradiction/support networks;
- provenance explanation;
- exploratory context assembly;
- open-world extension.

Therefore the design deliberately uses both.

## 8. Initial physical implementation recommendation

Do not introduce multiple infrastructure products immediately.

For the first backend implementation:

1. **Git/GitHub remains authoritative where current project/task truth already lives.**
2. Implement orchestration runtime state behind a storage interface.
3. Use a **single relational engine** for hot runtime state/event records when live concurrency needs exceed Git-CAS ergonomics; PostgreSQL is the preferred candidate because:
   - transactions and constraints support lease/CAS semantics;
   - adjacency tables + recursive CTEs support task DAG traversal;
   - JSONB supports versioned extension metadata;
   - materialized/read projections can coexist with normalized control tables.
4. Build the semantic graph initially as a **rebuildable in-memory/JSON/relational projection** over authoritative state.
5. Add a graph database only after measured query complexity or scale shows a material benefit.
6. Add a vector database only if semantic retrieval quality/latency cannot be met with existing search/indexing.

This is a recommendation, not a frozen technology selection.

## 9. Reasoning/execution separation types

### Reasoning outputs

- Finding
- Hypothesis
- Question
- DecisionRecord
- Plan
- DecompositionProposal
- CandidateAction
- EscalationProposal

Authority:
- epistemic/workflow only.

### Execution objects

- AuthorityDecision
- ActionSpec
- ActionClaim
- Attempt
- EffectReceipt
- ValidationResult
- Compensation
- TerminalActionResult

Authority:
- source-derived + deterministic gate only.

The transition from `CandidateAction` → `ActionSpec` is a critical trust boundary.

## 10. Efficient execution routing

The action compiler should choose the smallest capable executor after the reasoning decision is accepted.

Examples:
- deterministic computation → local process;
- Git mutation → GitHub/Git adapter;
- bounded shell operation → reviewed Workspace Shell profile;
- CI/build → GitRunner/GitHub Actions;
- document generation → artifact executor;
- research experiment → research-engine/PADataset runtime;
- reasoning-only → GPT-6 Instant worker;
- substantive judgment → human gate.

Do not use an LLM to execute something that can be represented as a deterministic typed action.

## 11. Execution feedback becomes reasoning evidence

Execution and reasoning are coupled through observations, not shared mutable prose.

Examples:
- CI FAIL becomes an Evidence/Observation + failed ActionAttempt.
- Experiment result becomes Result + Evidence.
- Permission denial becomes AuthorityBlocked observation.
- Partial write becomes EffectReceipt + repair/compensation state.
- Validator mismatch becomes feedback for REPAIR or re-reasoning.

The reasoning process then consumes these durable observations in the next quantum.

## 12. Evolutionary architecture requirement

This architecture MUST be revisited.

Required review triggers:
- after the first end-to-end real workflow completes through reasoning + execution;
- after representative workflows from at least three different domains run;
- after the first material concurrency/lease contention incident;
- after the first real execution rollback/compensation event;
- after enough real worker traces exist to identify recurring context/state-query patterns;
- before promoting a graph database, vector database, durable-workflow engine, or other new substrate;
- before production promotion.

Each review asks:
- Which data structures are carrying the wrong responsibility?
- Which projections are expensive or stale?
- Which state is ambiguous about authority?
- Where are duplicate representations diverging?
- Which queries dominate latency/complexity?
- Which failure/recovery patterns are awkward?
- Does a new substrate materially reduce complexity or improve correctness?

Pet ideas receive no special status. Measured workload and correctness win.

## 13. First implementation slice

Implement only the interfaces and data model needed to prove the separation:

1. EventRecord schema.
2. WorkItem / ReasoningProcess / edge schema.
3. DecisionRecord schema.
4. CandidateAction schema.
5. ActionSpec + EffectReceipt schema.
6. transactional transition/lease interface.
7. semantic projection interface.
8. packet/context compiler interface.
9. action compiler + authority gate interface.
10. one real workflow driven end-to-end.

Do not add a graph database, vector database, or general durable-workflow framework in this slice.

## 14. Success criterion

A successful system can:

- reason recursively across many GPT-6 Instant quanta;
- preserve compact durable cognitive state;
- decompose and synthesize work;
- convert conclusions into exact executable actions;
- execute effects exactly once/effectively once where possible;
- validate reality after execution;
- recover from failed workers/executors without repeating completed effects;
- explain why a decision and action occurred;
- evolve its storage/indexing architecture based on measured real workflows rather than architectural preference.
