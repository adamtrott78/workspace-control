# Workspace Semantic Execution Orchestrator Implementation Plan v0.1

Status: **PROPOSED / NON-AUTHORITATIVE IMPLEMENTATION PLAN**

Parent task: `workspace-semantic-execution-migration-v1`

Branch: `workspace-semantic-execution-migration-v1`

## 1. Objective

Convert the validated resumable-reasoning mechanics into a production-oriented Workspace Control orchestrator that:

- uses deterministic scheduling, state transitions, validation, waits, leases, and authority checks wherever reasoning is unnecessary;
- uses the lowest-scarcity capable semantic executor for bounded reasoning work;
- treats conversation continuity as an optimization rather than an authority or recovery dependency;
- supports persistent worker sessions with safe rotation back to durable state;
- distinguishes TOO_LARGE/decomposable work from INTRINSICALLY_DIFFICULT work;
- escalates reasoning tier only from durable evidence;
- keeps project-local truth and execution authority outside model inference;
- remains portable across model generations and execution surfaces;
- does not depend on browser automation of the consumer ChatGPT UI.

## 2. Current evidence baseline

Protocol screening P0-P3 established that durable externalized state, control-published results, objective validation, decomposition, critic/synthesizer role isolation, and stateless resume are mechanically viable.

For the hardest P3 mixed-long-hard fixture, C/D/E each completed with objective score 1.0 and zero violations. The hybrid E path completed with zero frontier escalations. This is protocol-screening evidence, not workspace-wide capability equivalence.

The implementation therefore proceeds from this hypothesis:

> Durable state + bounded reasoning + objective validation should be the default architecture; stronger reasoning is a routed exception, not the control plane.

## 3. Model-generation strategy

The core MUST NOT hard-code GPT-5.6, GPT-6, or any future model family.

The scheduler routes to capability/surface classes. Exact runtime identity is registry data.

Initial Chat calibration target:

- provider: OpenAI
- surface: ChatGPT Chat
- model: GPT-6 Sol
- configuration: Instant
- continuity: persistent worker session where safe; durable resume on rotation/failure
- programmatic invocation: false unless an explicitly supported OpenAI surface later provides it
- human launch required: true while ordinary Chat Instant lacks a documented machine invocation path

Suggested logical selector:

`OPENAI_CHAT_INSTANT_CURRENT`

Resolution must record the exact observed executor identity at invocation time. Replacing GPT-6 later should require recalibration, not scheduler redesign.

Official product evidence as of 2026-11:
- https://help.openai.com/en/articles/20001354-gpt-6-and-other-models-in-chatgpt
- https://help.openai.com/en/articles/6825453-chatgpt-release-notes

## 4. Consumer ChatGPT automation boundary

Production architecture MUST NOT rely on Selenium/Playwright/browser macros or simulated human input against the consumer ChatGPT UI.

Until OpenAI documents a supported programmatic invocation path for ordinary Chat Instant:

- Chat Instant is represented as a HUMAN_LAUNCHED or SUPPORTED_NATIVE_ONLY executor surface.
- The orchestrator may prepare an exact durable worker packet and select/reuse a session.
- The orchestrator may not fake keyboard/mouse activity, evade automation detection, bypass restrictions, or scrape output from the consumer UI.
- Fully unattended paths use supported APIs, local runtimes, GitHub/Work/Codex/native integrations, deterministic compute, or other documented machine interfaces.

Relevant OpenAI Terms:
- https://openai.com/policies/terms-of-use/

## 5. Semantic/ontology graph integration

The semantic graph is the shared meaning/provenance layer above the deterministic orchestrator. It is not the execution authority and it is not initially a separate graph database.

Authoritative project/task/workflow records are projected into the open-world semantic core defined by `workspace-semantic-execution-core.v0.1.json`.

The projection represents, among other things:

- goals, requirements, constraints, questions, findings and unresolved alternatives;
- work items, dependencies, decomposition and produced artifacts;
- evidence, provenance, contradiction and supersession;
- capabilities, reasoning/context/resource requirements;
- candidate actions;
- authority references and policy-derived gates;
- executors, sessions, attempts, results and validation.

The graph answers the questions needed by the orchestrator and packet compiler:

- WHAT_IS_CURRENT_OBJECTIVE
- WHAT_REMAINS_UNRESOLVED
- WHAT_WORK_DEPENDS_ON_THIS
- WHAT_IS_READY
- WHAT_IS_BLOCKED_AND_WHY
- WHAT_AUTHORITY_APPLIES
- WHAT_EXECUTOR_CAPABILITIES_ARE_REQUIRED
- WHY_WAS_THIS_EXECUTOR_SELECTED
- TRACE_ARTIFACT_TO_SOURCES_AND_ATTEMPTS

The control flow is therefore:

```text
project-local authoritative records
        ↓
rebuildable semantic/ontology projection
        ↓
bounded semantic slice for one ReasoningProcess
        ↓
deterministic authority + eligibility evaluation
        ↓
router / session broker
        ↓
executor
        ↓
result / evidence / artifact / validation
        ↓
authoritative record update where permitted
        ↓
projection refresh
        ↺
```

Critical boundary:

- semantic/model inference may create findings, alternatives, decomposition, requirements and CandidateActions;
- it may NOT create Permission, remove Prohibition, satisfy ReviewRequirement, or manufacture execution authority;
- AuthorityDecision remains deterministic/source-derived;
- the semantic graph can explain why an action is ready or blocked but cannot make itself authorized.

For v0, use a rebuildable JSON/JSONL or in-memory projection and existing durable stores. Do not add a graph database until measured query/context/routing needs justify one.

### Semantic packet compiler

The packet compiler should query the semantic projection rather than dumping task history.

For each worker it should select only the smallest relevant neighborhood:

- current ReasoningProcess;
- parent objective and inherited constraints;
- live findings/hypotheses/questions;
- direct dependencies and blockers;
- exact evidence refs;
- authority/gate refs;
- required capabilities and validator;
- recent superseding events;
- next safe boundary.

This is the mechanism that makes persistent Instant sessions optional rather than necessary.

## 6. Operator UX and manual Chat Instant bridge

The human-operated portion of Chat Instant MUST be designed as a low-attention mechanical bridge, not as an expert operator workflow.

Primary UX objective:

> Minimize human decisions, typing, navigation, state interpretation and repeated copy/paste while staying inside supported ChatGPT interaction boundaries.

The orchestrator should automate everything outside the consumer ChatGPT UI:

- decide which worker/session is next;
- decide whether to reuse or rotate a session;
- construct the exact packet;
- place the packet on the clipboard or expose one-copy UI;
- show the assigned worker/session label;
- show only one next action;
- detect durable worker output through GitHub/state changes;
- validate the result;
- prepare the next packet automatically;
- maintain counters, progress and blockers;
- never require the human to relay SHAs, JSON, logs, experiment results or state manually.

The manual bridge should ideally require only:

1. open/select the indicated existing ChatGPT Instant conversation, or create one when rotation is required;
2. paste the already-prepared packet;
3. submit it;
4. return to the orchestrator when notified that the durable state changed.

Target operator interactions:
- zero manual transcription;
- zero manual state interpretation;
- zero manual prompt editing;
- zero manual model-selection decisions during a run after session setup;
- one clipboard paste + one submit per required Chat turn;
- reuse persistent sessions for multiple quanta where isolation is not required;
- new chat creation only on explicit rotation conditions.

### Operator console

Build a small operator console/CLI/UI that presents:

- task name;
- worker/session label;
- model/config required;
- reuse existing session vs create new session;
- one-click/copy packet;
- concise status: READY / SENT / WAITING / RESULT DETECTED / ROTATE / DONE;
- human-launch count;
- remaining estimated manual turns;
- last durable checkpoint;
- any real authority or judgment gate.

The console should hide ordinary control-plane detail unless expanded.

### Session slot model

Use stable logical slots such as:

- instant-general-1
- instant-general-2
- critic-1
- synthesizer-1

A slot persists across many quanta and is mapped to a Chat conversation by the human once. The orchestrator records only non-secret session metadata and durable checkpoint affinity; it does not scrape or control the consumer UI.

Rotation reasons must be explicit and machine-generated:
- CONTEXT_LIMIT;
- ROLE_ISOLATION;
- CONTINUITY_LOST;
- MODEL_CHANGED;
- TOOLSET_CHANGED;
- VALIDATOR_FAILURE_LOOP;
- POLICY_REQUIRES_FRESH;
- USER_REQUESTED.

### UX acceptance metrics

Measure:
- manual launches per completed workflow;
- manual pastes/submits per completed workflow;
- percentage of turns reusing an existing session;
- operator decisions required;
- manual transcription count;
- time spent interpreting control state;
- accidental wrong-session rate;
- continuity-loss recovery effort.

A production-worthy bridge should make repeated Instant use feel like servicing a queue, not operating the control plane.

## 7. Target control loop

```text
authoritative task/workflow state
        ↓
semantic projection / bounded context
        ↓
deterministic eligibility + authority
        ↓
routing decision
        ↓
executor/session selection
        ↓
reasoning packet
        ↓
executor invocation
        ↓
typed transition proposal/result
        ↓
deterministic transition validation
        ↓
durable commit/event
        ↓
validator / external wait / next ready work
        ↺
```

No model owns the loop.

## 8. Implementation phases

### Phase 0 — Close benchmark stage and synchronize authority

Deliverables:
- reconcile the task capsule with completed P3 A-E screening;
- preserve screening claim limits;
- record the P3 C/D/E score-1.0 verdict and zero-frontier-escalation result;
- record remaining claim-bearing benchmark gates separately from implementation work;
- regenerate the derived handoff Markdown;
- validate exact-head task state.

Exit gate:
- task capsule and handoff agree on the completed screening checkpoint and next implementation stage.

### Phase 1 — Deterministic orchestration kernel

Implement the minimum generic state engine.

Core entities:
- WorkItem
- ReasoningProcess
- Attempt
- Lease
- Event
- WaitCondition
- RoutingDecision
- ExecutorSession
- ValidationResult
- Artifact/Result reference

Required transitions:
- READY
- CLAIMED
- RUNNING
- WAITING_EXTERNAL
- READY_TO_RESUME
- TERMINAL_CANDIDATE
- VALIDATING
- COMPLETED
- FAILED
- AUTHORITY_BLOCKED

Required mechanics:
- CAS / generation fencing;
- idempotent transition validation;
- stale-worker rejection;
- bounded retry policy;
- no model polling during waits;
- immutable event/evidence references;
- fail-closed unknown transitions.

Exit gate:
- deterministic tests reproduce the successful P3 wait/resume, stale-generation, and terminal-validation mechanics without a live model.

### Phase 2 — Executor registry and resource router

Turn `workspace-semantic-execution-executor-resource.v0.1.json` into executable registry/router code.

Initial executor classes:
- DETERMINISTIC
- LOCAL_MODEL
- OPENAI_CHAT_INSTANT
- SUPPORTED_OPENAI_AGENT
- PAYG_API
- FRONTIER_REASONING
- HUMAN

Registry identity includes:
- provider
- exact model
- surface
- harness
- toolset
- capability profile
- privacy/locality
- session semantics
- programmatic invocation support
- usage pools

Routing invariants:
- importance does not imply stronger model;
- TOO_LARGE => DECOMPOSE;
- INTRINSICALLY_DIFFICULT => evidence-gated escalation;
- external wait => no reasoning executor;
- unknown quota => UNKNOWN, never fabricated;
- execution authority is filtered before routing.

Exit gate:
- deterministic routing tests select the expected executor for P0-P3-style synthetic requirements and fail closed on unsupported surfaces.

### Phase 3 — Reasoning packet compiler

Compile durable semantic state into bounded model packets.

Packet includes:
- exact task/process identity;
- source checkpoint;
- current objective;
- known findings;
- unresolved hypotheses/questions;
- authority constraints;
- allowed tools/actions;
- exact evidence refs;
- validator contract;
- required output/transition schema;
- next safe boundary.

Default:
- full chat transcript is NOT required;
- raw evidence is retrieved progressively;
- packet is reproducible from durable state.

Exit gate:
- reconstruct equivalent worker packets after deleting all conversational context.

### Phase 4 — Persistent session broker

Add session reuse as an optimization.

Session record:
- executor identity
- role
- task/process affinity
- created_at / last_used
- quanta count
- approximate context load
- tool availability
- health/continuity
- durable checkpoint last acknowledged

Reuse policy:
- reuse a compatible persistent Instant session for multiple quanta;
- rotate on role-isolation requirement, context threshold, continuity loss, repeated validator failure, tool mismatch, model change, or policy requirement;
- after rotation, rebuild from durable state rather than attempting chat-memory reconstruction.

Important:
- Chat session is a cache.
- Durable state is the source of recovery.

Exit gate:
- a simulated session can disappear mid-run and a replacement resumes without replaying completed work.

### Phase 5 — Executor adapters

Implement adapters in safety order.

5A. Deterministic adapter
- Python/process validators;
- Git/GitHub observation;
- CI/result ingestion;
- artifact/hash checks.

5B. Local model adapter
- programmatic local inference;
- calibrated extraction/classification/bounded reasoning.

5C. Supported API/agent adapter
- documented machine invocation only;
- exact model/surface/usage accounting.

5D. Chat Instant bridge
- initially human-launched;
- emits exact worker packet and session assignment;
- ingests only durable worker-authored repository state;
- no consumer-UI automation.

A future OpenAI-supported Chat invocation path may replace the human launch bridge without changing scheduler semantics.

Exit gate:
- same ReasoningProcess can route through at least two machine adapters and the Chat human-launch bridge without changing its workflow schema.

### Phase 6 — Event-driven waits and validator service

Implement:
- event subscriptions / wake keys;
- WAITING_EXTERNAL registry;
- result publication contracts;
- objective validator interface;
- terminal validation;
- validator feedback repair loop;
- no polling by reasoning workers.

Exit gate:
- P3-like six-experiment workflow completes in simulation with zero reasoning calls while waiting.

### Phase 7 — GPT-6 Sol / Instant calibration

Do NOT rerun the entire painful manual screening matrix.

Run a focused GPT-6 calibration set:
- P0 easy control;
- P2 coupled reasoning;
- P3 mixed long/hard;
- one unseen-workflow extension.

Compare:
- objective score;
- reasoning quanta;
- retries;
- decomposition correctness;
- false escalation;
- context size;
- session rotations;
- human launch count.

Primary question:
- can GPT-6 Sol / Instant inherit the Instant-default role with equal or better validated reliability?

Exit gate:
- GPT-6 Instant has capability evidence for the classes we intend to route to it.

### Phase 8 — Shadow-mode production pilot

Run orchestrator beside existing Workspace Control.

Rules:
- no autonomous high-consequence actions;
- scheduler emits proposed routing/transition decisions;
- existing workflow remains authoritative;
- compare predicted next action against actual operator/controller path.

Pilot workflows:
- repository/CI maintenance;
- bounded research iteration;
- one course/tutoring workflow;
- one document/artifact workflow.

Exit gate:
- no authority escapes, no stale completions, no lost waits, and acceptable routing agreement.

### Phase 9 — Bounded autonomous pilot

Enable automatic execution only for already-authorized reversible classes.

Examples:
- deterministic validation;
- read-only state inspection;
- supported GitHub writes within exact task scope;
- local/API reasoning workers;
- event-driven resume.

Chat Instant remains human-launched until OpenAI provides a supported automation path.

Exit gate:
- multi-day workflow completes with durable recovery and minimal operator attention.

### Phase 10 — Architecture freeze / promotion

Freeze only after:
- claim-bearing replicated benchmark evidence;
- independent architecture review;
- unseen extension proof;
- authority/security review;
- rollback proof;
- shadow + bounded autonomous pilot success.

## 9. Immediate build order

The first implementation slice should be deliberately small:

1. synchronize the completed benchmark state;
2. create state-machine schemas;
3. implement transition validator + CAS/generation fencing;
4. implement deterministic event/wait loop;
5. implement semantic projection/query layer over existing durable state;
6. implement executor registry;
7. implement semantic packet compiler;
8. implement persistent session broker;
9. implement the low-attention operator console and human-launched Chat Instant bridge;
10. wire one fully machine-invoked executor;
11. replay P3 from recorded evidence with no manual control-plane decisions and minimal human Chat interaction;
12. then calibrate GPT-6 Sol / Instant.

## 10. Non-goals for v0

Do not:
- build a graph database;
- replace research-engine/PostgreSQL;
- replace GitRunner;
- replace Workspace Shell;
- build a general-purpose agent framework;
- automate consumer chatgpt.com;
- optimize every workflow family at once;
- make strong Instant-vs-frontier equivalence claims from screening data.

## 11. Success criterion

The v0 orchestrator is successful when a user can submit one durable task and the system can:

- select a suitable low-scarcity executor;
- run/resume bounded reasoning;
- survive worker/session loss;
- wait without model burn;
- validate results objectively;
- decompose oversized work;
- escalate only with evidence;
- preserve authority and provenance;
- require human involvement only for a real authority/judgment gate or an unsupported human-launched execution surface.

The human should no longer act as the message bus.
