# Workspace Semantic Execution — Architecture Research Review v0.1

Status: **RESEARCH REVIEW / PROVISIONAL RECOMMENDATION / NOT FROZEN**

Parent task: `workspace-semantic-execution-migration-v1`

Date: 2026-11-13

## Executive conclusion

The prior "custom append-only event log + relational current state + semantic graph projection" design is directionally correct at the logical level, but **should not be implemented as a hand-built durable-execution engine by default**.

The strongest evidence from durable-workflow systems and recent agent research suggests a three-plane architecture:

1. **Cognitive plane** — hierarchical external reasoning across strategic, tactical, and operational timescales, with explicit context distillation and externally validated feedback.
2. **Durable execution plane** — use a proven durable-execution runtime for checkpointing, retries, waits/signals, concurrency, idempotency, and recovery instead of reimplementing event sourcing/replay.
3. **Knowledge/state plane** — use fit-for-purpose application state: transactional relational state for authoritative control, a typed DAG for work structure, immutable evidence/artifact refs, and a rebuildable temporal semantic graph for reasoning/context/provenance.

This review does **not** freeze a specific durable runtime yet. DBOS is the leading first-spike candidate because Workspace Control already expects PostgreSQL-like state, DBOS is Postgres-native, offers queues/concurrency/messages/events, workflow-ID idempotency, and exactly-once database transactions. Restate is the leading alternative where cheap long suspension, durable promises, keyed state, and low-latency durable RPC dominate. Temporal remains the maturity/reference ceiling but imposes materially more operational/runtime complexity.

The runtime decision should be made by one **real end-to-end Workspace Control workflow**, not a synthetic benchmark campaign.

## 1. External reasoning: what survives scrutiny

The literature strongly supports externalizing reasoning into a harness rather than expecting one monolithic model call.

### Positive evidence

- **Self-Refine (NeurIPS 2023)**: repeated generation -> feedback -> refinement improves outputs without retraining.
- **Reflexion (NeurIPS 2023)**: stores linguistic feedback in episodic memory and improves later attempts.
- **RAP (EMNLP 2023)** and **LATS (ICML 2024)**: externalize search/planning into explicit trees and environment-feedback loops.
- **Graph of Thoughts (AAAI 2024)**: models intermediate reasoning as a graph with aggregation and feedback edges.
- **Test-time compute scaling (ICLR 2025)**: adaptive inference-time search can outperform substantially larger models for suitable task difficulty regimes; optimal compute allocation is prompt-dependent.
- **Recursive Language Models (2025)**: recursively inspect/decompose external context instead of forcing all information through one monolithic context.
- **COMPASS (ACL 2026)**: tactical agent + asynchronous Meta-Thinker + Context Manager; reports up to 20% relative improvements on long-horizon benchmarks.
- **MOSAIC (NeurIPS 2026, Microsoft Research)**: explicitly separates strategic, tactical, and operational time scales with scale-specific context and adaptive inference budgets; reports 38–57% inference-token reduction versus flat ReAct baselines.
- **Externalization in LLM Agents (2026 survey)**: frames memory, skills, protocols, and harnesses as external cognitive infrastructure that moves burdens out of model weights/one-shot inference.

### Important negative evidence

External cycles are **not automatically useful**.

- ICLR 2024 and TACL 2024 analyses find intrinsic self-correction without reliable external feedback can fail or degrade reasoning.
- ICML 2024 analysis of multi-agent debate finds debate does not reliably beat simpler self-consistency/ensembling without careful protocol tuning.
- 2026 multi-agent fault work shows semantic communication faults can silently propagate through agent networks.
- Agents of Chaos (2026) documents real agent failures including destructive effects, unauthorized actions, runaway resource use, and agents claiming completion while environment state contradicted them.

### Consequence

The system should not "ask Instant to think again."

A new reasoning quantum is justified only when at least one of these changed:
- evidence/observation;
- validator feedback;
- context slice;
- branch/hypothesis;
- decomposition structure;
- critic finding;
- child result;
- authority/resource state.

The basic unit should be **validated state transition per reasoning quantum**, not "number of turns."

## 2. Reasoning hierarchy should be multi-scale

The earlier worker/critic/synthesizer split is useful but incomplete.

Research supports three semantic time scales:

### Strategic process
Low-frequency.
Owns:
- global objective;
- major constraints;
- decomposition policy;
- unresolved high-coupling decisions;
- resource/escalation policy;
- global progress and replanning.

### Tactical process
Medium-frequency.
Owns:
- one subgoal/workstream;
- local planning;
- evidence integration;
- child decomposition;
- critic/repair cycles;
- hierarchical synthesis.

### Operational process
High-frequency.
Owns:
- exact action preparation;
- bounded tool execution;
- observations;
- local postcondition checks;
- durable receipts.

Context should be distilled separately for each level instead of sharing one ever-growing transcript.

GPT-6 Instant can potentially execute any of these roles when the node fits the calibrated envelope; stronger effort is a property of a residual reasoning node, not a permanent "manager model."

## 3. Multi-agent architecture: centralized shared state, not free-form society

The research does **not** support building a large peer-to-peer chat society.

Reasons:
- communication channels grow rapidly with worker count;
- free-form natural-language messages can silently lose/alter evidence;
- debate is protocol-sensitive and not inherently superior;
- correlated model bias can survive or amplify through repeated self-critique.

Preferred topology:

```text
                    STRATEGIC PROCESS
                         |
               durable typed state
                         |
        +----------------+----------------+
        |                |                |
   TACTICAL A       TACTICAL B       TACTICAL C
        |                |                |
     leaves            leaves           leaves
        |                |                |
  validators        validators       validators
        +----------------+----------------+
                         |
                  typed synthesis
```

Workers communicate primarily through:
- typed records;
- immutable evidence refs;
- validation results;
- structured decisions;
- task DAG state.

Natural-language free-form peer messages are optional evidence, not authoritative shared state.

## 4. Durable execution: do not reinvent replay/recovery first

Multiple mature systems independently converge on the same primitives:
- durable journal/history;
- deterministic orchestration/replay or checkpoints;
- side-effecting activities/steps;
- signals/messages/callbacks;
- timers/waits;
- child workflows / parallel maps;
- idempotency keys;
- at-least-once effect handling;
- saga/compensation for partial distributed effects.

### Temporal
Strengths:
- most mature/reference architecture;
- event history + deterministic replay;
- excellent Signals/Updates, child workflows, Activities, timers, sagas;
- strong failure semantics and operational tooling.

Costs:
- separate Temporal service/cluster;
- deterministic workflow constraints;
- more operational complexity than this project likely needs initially.

### DBOS
Strengths:
- durable workflows built directly on PostgreSQL;
- no separate orchestration server required for basic deployment;
- workflow IDs are idempotency keys;
- transactions can commit application writes + workflow durability exactly once;
- durable queues with global/worker/partition concurrency and rate limits;
- send/recv messaging, events, human-in-loop patterns;
- external steps are at-least-once, with checkpointed completed steps.

Risks:
- workflow code still has deterministic constraints;
- external side effects remain idempotency-sensitive;
- some suspension behavior differs by deployment/product tier;
- younger than Temporal.

### Restate
Strengths:
- single-binary durable runtime;
- purpose-built journal/log;
- durable RPC/messages/promises/timers;
- keyed Virtual Objects with serialized state updates;
- explicit AI-agent integrations;
- cheap long-running suspension and low per-action latency;
- strong fit for durable sessions and callbacks.

Risks:
- separate specialized durable store from PostgreSQL/application state;
- more cross-store consistency design if relational project state remains Postgres;
- younger ecosystem than Temporal;
- server licensing/operational choice should be reviewed.

### AWS/Durable Task/Dapr
Technically capable, but less aligned with current local/portable Workspace Control constraints or introduce provider/runtime coupling not currently justified.

### Provisional runtime choice

**DBOS should get the first real-workflow implementation spike**, not because it is permanently selected, but because:
- PostgreSQL is already a natural fit for the application's authoritative hot state;
- exact transactional coupling between workflow progress and application state is unusually valuable here;
- it minimizes new infrastructure;
- its queue/concurrency/idempotency/message model maps directly onto the Instant-worker army.

Keep the durable-runtime boundary abstract enough that Restate or Temporal can replace it if the real workflow exposes weak long-wait/recovery/versioning behavior.

## 5. Event sourcing / CQRS: use runtime history, not duplicate every internal event

The previous proposal risked creating:
1. custom event journal;
2. mutable current-state tables;
3. durable-runtime history;
4. Git task history.

That is too many partially overlapping truths.

Microsoft's CQRS/Event Sourcing guidance explicitly warns of added complexity, eventual consistency, projection costs, and snapshot/replay concerns.

Revised rule:

- **Durable runtime journal/history owns low-level execution replay.**
- **Application relational tables own current domain/control state.**
- **Domain audit events record only semantically meaningful state changes** (DecisionRecorded, ActionAuthorized, EffectObserved, ValidationFailed, WorkCompleted, etc.).
- **Git remains authoritative where project/task contracts already live.**
- **Semantic graph is rebuilt from authoritative domain/project/evidence records.**

Do not replicate every runtime journal entry into a custom application event store.

## 6. Execution plane: strongest part of the previous design

Research reinforces the CandidateAction -> deterministic ActionSpec trust boundary.

Durable-execution documentation repeatedly warns that a step may execute externally and crash before its completion is recorded. Therefore "exactly once execution" is generally impossible for arbitrary external effects; the safe patterns are:
- idempotent effects;
- stable idempotency keys;
- transactional coupling when both state and effect live in one database;
- at-most-once semantics for non-repeatable effects where supported;
- compensating actions/sagas where partial rollback is meaningful.

Therefore each executable action should bind:

- action_id;
- exact target/resource/version;
- source ReasoningProcess/DecisionRecord;
- authority decision;
- immutable evidence/input refs;
- preconditions;
- executor/tool identity;
- idempotency key or explicit non-idempotent semantic;
- expected effects;
- timeout/retry class;
- compensation if applicable;
- postcondition validator.

**Tool success != task success.**

Effect completion requires observed postcondition evidence.

This is directly supported by real-agent red-team evidence where agents sometimes reported completion despite contradictory system state.

## 7. State/memory: one universal graph is not supported by the evidence

Research strongly supports structured external memory, but not one storage structure for everything.

Relevant results:
- MemGPT uses memory tiers / virtual-context management.
- Generative Agents uses episodic observations, higher-level reflections, and dynamic retrieval.
- A-MEM (NeurIPS 2025) dynamically links and evolves notes into a knowledge network.
- Zep/Graphiti uses a temporal knowledge graph for dynamic cross-session facts.
- MOSAIC-style memory work emphasizes graph structure/conflict handling.
- Recent surveys distinguish factual/semantic, experiential/episodic, and working memory functions.
- Agent Zero Memory (2026 preprint) explicitly argues that a single fact store, vector index, or graph inherits blind spots, and uses three parallel representations: event timeline, entity-event graph, and curated documentary memory.

### Recommended memory mapping

#### Working memory
- compact current ReasoningProcess state;
- short-lived;
- relational/JSON typed record;
- directly packet-compiled.

#### Episodic / execution memory
- attempts;
- decisions;
- effects;
- validator results;
- failures;
- workflow episodes;
- durable runtime + domain records.

#### Semantic memory
- findings;
- claims;
- entities;
- relationships;
- requirements;
- support/contradiction;
- temporal/supersession relationships;
- semantic ontology graph.

#### Procedural memory
Future:
- validated reusable skills/patterns compiled from successful traces;
- versioned;
- evidence-backed;
- not automatically promoted from one successful run.

This separation is more defensible than "the ontology graph stores the agent's memory."

## 8. The semantic ontology graph still belongs — but as a temporal/provenance read model

The graph should remain because it is well matched to:
- cross-domain relationships;
- evidence/support/contradiction;
- provenance;
- dependency explanation;
- context retrieval;
- historical/current semantic facts;
- "why" questions.

It should **not** own:
- atomic task claims;
- lease fencing;
- exact action lifecycle;
- queue semantics;
- permission granting;
- external-effect completion.

### Important refinement: bitemporal semantics

Temporal knowledge-graph work suggests recording at least:
- **valid time**: when the fact/relationship is true in the world/project;
- **record time**: when Workspace Control learned/recorded it.

Our semantic assertions should distinguish these instead of treating time as one timestamp.

That supports:
- "what did we believe then?";
- "what was actually true then?";
- supersession without deletion;
- contradiction handling;
- historically correct packet reconstruction.

## 9. Physical storage recommendation

Do not choose Neo4j/vector DB yet.

Initial physical design can plausibly use PostgreSQL for:
- authoritative current domain state;
- typed DAG nodes/edges;
- DecisionRecords;
- ActionSpecs/receipts/validations;
- bitemporal semantic node/edge projection;
- JSONB extension metadata;
- full-text and optionally pgvector retrieval later.

PostgreSQL already provides:
- transactions/Serializable isolation;
- row locking;
- `SKIP LOCKED` for queue-like multi-consumer access;
- recursive SQL for hierarchical/graph traversals;
- GIN indexing over JSONB.

A dedicated graph DB becomes justified if real workloads show:
- deep/many graph traversals dominate;
- relational recursive queries become operationally painful;
- graph query expressiveness materially improves development/retrieval quality;
- measured performance cannot meet packet-compilation needs.

## 10. Authority/policy plane

Do not mix authority into the semantic graph.

Cedar and OPA both illustrate the industry pattern:
- policy decision is a separate deterministic service/module;
- application is the enforcement point;
- default deny/fail closed;
- policy logic is separable from business/reasoning logic.

For Workspace Control:
- keep an `AuthorityEvaluatorPort`;
- continue using existing authority-owned task/policy contracts first;
- evaluate Cedar/OPA only when policy complexity justifies a dedicated language/runtime.

Do not add a policy engine merely for architectural neatness.

## 11. Recommended first real workflow

Use the **semantic-execution backend implementation itself** as the first proving workload.

The workflow should exercise:

1. strategic reasoning chooses one backend slice;
2. tactical process decomposes it;
3. multiple GPT-6 Instant leaves research/implement/review;
4. deterministic validators/CI evaluate each effect;
5. external wait returns control with zero model polling;
6. failed validation creates new evidence and a repair quantum;
7. accepted child outputs are synthesized;
8. one or more typed ActionSpecs mutate the repository through existing GitHub authority;
9. effects are validated against exact Git/CI state;
10. the system records all decisions/evidence/receipts and resumes after at least one simulated worker/session loss.

This gives useful project progress while simultaneously testing the architecture.

## 12. Decision gates after that workflow

Before freezing the runtime/storage architecture, inspect:

- How awkward was workflow modeling in DBOS?
- Did external waits require unacceptable process retention or product-tier features?
- Did transactional coupling to PostgreSQL simplify correctness materially?
- Did we need custom queues/leases beyond DBOS?
- Did the semantic projection query pattern fit relational nodes/edges?
- How often did context assembly need multi-hop graph traversal?
- Did repeated GPT-6 Instant cycles benefit from separate strategic/tactical state?
- Were independent critics useful or redundant?
- Did typed records prevent coordination loss?
- Were any effects difficult to make idempotent?
- Did Git + runtime DB create authority/source-of-truth ambiguity?
- Which telemetry actually predicted failure/escalation?

Only then:
- freeze DBOS;
- switch to Restate/Temporal;
- add graph DB;
- add vector DB;
- or revise the cognitive hierarchy.

## 13. Research sources reviewed

Durable systems / execution:
- Temporal Event History, Workflows, Activities, Signals/Updates, Child Workflows, design patterns.
- DBOS architecture, workflows, transactions, queues, workflow communication, HITL.
- Restate durable runtime, journals, Virtual Objects, durable promises/RPC, AI agent integrations.
- AWS Durable Execution callbacks, waits, idempotency/retry semantics.
- Microsoft Durable Task replay/orchestrator model.
- Microsoft CQRS/Event Sourcing architecture guidance.
- PostgreSQL transactions, Serializable isolation, row locks/SKIP LOCKED, JSONB/GIN.

Reasoning / agents:
- Self-Refine, NeurIPS 2023.
- Reflexion, NeurIPS 2023.
- RAP, EMNLP 2023.
- Graph of Thoughts, AAAI 2024.
- LATS, ICML 2024.
- Test-time compute scaling, ICLR 2025.
- A-MEM, NeurIPS 2025.
- Recursive Language Models, 2025.
- COMPASS, ACL 2026.
- MOSAIC adaptive multi-scale inference, NeurIPS 2026.
- Externalization in LLM Agents, 2026 survey.
- Code as Agent Harness, 2026 survey.
- Memory in the Age of AI Agents, 2025/2026 survey.
- Horizon Gap, 2026 survey.
- Self-correction limitations, ICLR/TACL 2024.
- Multi-agent debate analysis, ICML 2024.
- Agents of Chaos, 2026 red-team preprint.
- Multi-agent communication-fault study, 2026 preprint.

Memory / provenance:
- W3C PROV-O.
- MemGPT.
- Generative Agents.
- Zep/Graphiti temporal knowledge graph.
- Agent Zero Memory (2026 preprint).
- recent agent-memory surveys.

## 14. Provisional architecture recommendation

```text
                  STRATEGIC REASONING
                         |
               distilled durable state
                         |
                 TACTICAL PROCESSES
                  /      |       \
             worker   worker   critic
                  \      |       /
                   validated results
                         |
                 tactical synthesis
                         |
                   CandidateAction
                         |
             deterministic authority
                  + action compiler
                         |
                DURABLE RUNTIME
          (DBOS first real-workflow spike)
                         |
                   effect adapter
                         |
                observed postcondition
                         |
                    validation
                         |
             durable domain state
                         |
       +-----------------+----------------+
       |                 |                |
  working state      episodic state   semantic graph
  (typed current)   (decisions/effects) (temporal projection)
       |                 |                |
       +-----------------+----------------+
                         |
                  context compiler
                         ↺
```

This is a research-backed provisional architecture, not a frozen implementation contract.
