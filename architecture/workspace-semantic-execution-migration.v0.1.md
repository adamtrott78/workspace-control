# Workspace Semantic Execution Migration v0.1

Status: **DRAFT / NON-AUTHORITATIVE DESIGN INVENTORY**

Branch: `workspace-semantic-execution-migration-v1`

Base: `workspace-control@d47a7922aa8d47d3a22b55c19ce4d6af7309a964`

## Purpose

Workspace Control has evolved beyond a task runner. It now coordinates or supports:

- scientific research and iterative experimentation;
- software and systems engineering;
- data-science workflows;
- paper composition and revision;
- presentation and slide production;
- repository-backed tutoring and coursework;
- document/report/cheat-sheet/resume production;
- validation, review, runtime certification, CI, and controller operations;
- evidence-first architecture and implementation research.

The existing execution model assumed that capable frontier reasoning could be invoked broadly and repeatedly without materially scarce usage accounting. That assumption is changing.

The next architecture must preserve the current autonomous behavior while treating scarce frontier-model allowance as a schedulable resource. It must exploit deterministic execution, unmetered or low-cost interactive executors, local models, future subscription executors, and frontier reasoning selectively.

This document records the migration problem, existing evidence across the workspace, the required common architecture, and the extensibility contract needed so Workspace Control can continue to grow without another foundational rewrite.

This document does **not** grant execution authority, modify project truth, change production routing, or supersede existing task capsules, policies, procedures, or project-local contracts.

---

## 1. Core problem

The required replacement is not a research-only system and not a coding-agent scheduler.

The system must support a general cognitive-work lifecycle:

```text
INTENT
  ↓
CONTEXT ACQUISITION
  ↓
SEMANTIC UNDERSTANDING
  ↓
PLAN / STRUCTURE / DECOMPOSITION
  ↓
PRODUCE OR EXECUTE SOMETHING
  ↓
OBSERVE RESULT
  ↓
EVALUATE AGAINST REQUIREMENTS
  ↓
REVISE / EXPAND / DECOMPOSE / ESCALATE
  ↺
  ↓
DELIVERABLE / DECISION / VERIFIED STATE
```

Different domains instantiate this lifecycle differently:

### Research

```text
question
→ literature/evidence
→ hypothesis
→ experiment
→ execution
→ analysis
→ finding
→ belief update
→ next experiment
```

### Software and systems engineering

```text
objective
→ architecture
→ implementation
→ tests
→ CI
→ diagnosis
→ repair
→ review
→ deployment / checkpoint
```

### Data science

```text
question
→ data acquisition
→ cleaning
→ EDA
→ modeling
→ evaluation
→ interpretation
→ error analysis
→ revised hypothesis/model
```

### Paper creation

```text
evidence
→ claim boundaries
→ argument structure
→ source/exemplar analysis
→ draft
→ figures/tables
→ citation verification
→ reviewer-style audit
→ revision
→ final build
```

### Presentation creation

```text
purpose + audience
→ narrative
→ slide plan
→ evidence selection
→ visual production
→ assembly
→ render
→ visual QA
→ script
→ revision
→ final deck
```

### Tutoring and coursework

```text
course authority + student state
→ skill/dependency graph
→ diagnosis
→ teaching / assignment work
→ behavioral evidence
→ artifact production
→ mastery update
→ assessment preparation
→ later retention / transfer
```

The new architecture must support all of these without hard-coding one orchestration engine per domain.

---

## 2. Existing workspace evidence

The migration is not a clean-room rebuild. The repositories already contain specialized implementations of many required abstractions.

### 2.1 workspace-control

`workspace-control` already owns reusable cross-project behavior including:

- `policies/TUTORING_CONTRACT.md`;
- `policies/OPERATOR_WORKFLOW.md`;
- `policies/PORTABILITY_CONTRACT.md`;
- `procedures/document_artifact_build.md`;
- `procedures/evidence_first_solution_research.md`;
- `procedures/runtime_certification.md`;
- `procedures/scope_closure.md`;
- `procedures/validation_routing.md`;
- `procedures/task_capsule.md`;
- course bootstrap, ingestion, study, assignment, assessment, cheat-sheet, communications, and document workflows;
- controller, GitHub Actions, runtime, review, and validation architecture.

The tutoring contract already proves that Workspace Control needs semantic distinctions that cannot be reduced to generic task state:

```text
artifact correctness ≠ student mastery
assignment completion ≠ mastery
source ingestion ≠ mastery
compiler success ≠ artifact correctness
repository completion ≠ external submission
```

The generic document-artifact procedure already defines a reusable artifact loop:

```text
load domain contract
→ prepare source
→ deterministic build
→ structural/static validation
→ render
→ visual QA
→ bounded revision
→ delivery gate
```

The evidence-first solution-research procedure already defines a generic architecture-research loop:

```text
problem framing
→ recover local evidence
→ current external research
→ architecture-family synthesis
→ system-boundary impact review
→ bounded shortlist
→ benchmark/promotion contract
→ implementation
```

These are reusable semantic workflows, not merely chat instructions.

### 2.2 PADataset

`PADataset` already contains a mature research framework spanning:

- waveform generation;
- OTA capture;
- preprocessing/banking/caching;
- model training;
- open-set evaluation;
- experiment manifests;
- result analysis;
- figure/table generation;
- paper composition;
- presentation production;
- provenance and repository/runtime boundaries.

Its root workflow explicitly distinguishes scientific/data contracts, historical implementation, and recommended future operation.

Its paper methodology is already an iterative cognitive-production workflow:

```text
scientific ground truth
→ evidence-driven draft
→ role-based exemplar library
→ individual source analysis
→ transferable heuristic synthesis
→ targeted revision
→ reviewer scoring/audit
→ page-budget clarity optimization
→ hostile-reader pass
→ human + mechanical verification
```

The MILCOM presentation branch further demonstrates that slide production is a structured workflow with:

- presentation plan;
- PPTX assembly;
- SVG production specification;
- per-slide sources;
- visual assets;
- previews;
- build tools;
- speaker script;
- presenter study guide;
- rescue/revision plan.

Paper and presentation creation therefore require first-class semantic and artifact workflows, not a generic `MAKE_DOCUMENT` task.

### 2.3 research-engine

`research-engine` already implements a durable research orchestrator with:

- PostgreSQL-backed state;
- executor tiers;
- job types;
- dependency handling;
- idempotency keys;
- worker registration;
- leases;
- lease expiry;
- attempt counts;
- retries;
- deterministic and semantic executors;
- local-model routing;
- provenance-first evidence handling;
- semantic graph and artifact-store components.

Current executor tiers include:

```text
DETERMINISTIC
CHEAP
STANDARD
STRONG
HUMAN
```

Current research job types include:

```text
DISCOVERY
SCREEN
ACQUIRE
EXTRACT
VERIFY
CHECKPOINT
SYNTHESIZE
GAP_GENERATE
NOVELTY_SEARCH
NOVELTY_ARBITRATE
HUMAN_REVIEW
```

This is a strong candidate foundation for a generalized durable execution kernel, but its job taxonomy is research-specific and its executor routing assumptions must become heterogeneous and usage-aware.

### 2.4 Course repositories

The course repositories demonstrate real domain adapters rather than hypothetical ones.

#### MTH602

The active tutoring branch contains:

- course/instructor authority;
- source ingestion routes;
- tutoring modes;
- skill map;
- mastery snapshot;
- mastery history;
- assignment context;
- learning records;
- computational source;
- numerical result provenance;
- reports;
- assessment prep;
- artifact QA;
- explicit external-submission gates.

Homework 3 alone mixes:

- exact source provenance;
- instructor-specific deadline exceptions;
- handwritten-vs-computational deliverable rules;
- textbook/reference authority;
- mathematical derivations;
- numerical experiments;
- plots;
- report production;
- tutoring/mastery state.

#### EAS501 and CIS560

Their tutoring branches instantiate the same broader architecture with course-specific content, skills, mastery, study, homework, and assignment semantics.

These repositories prove that the new system must support domain-specific semantic state while preserving shared execution behavior.

---

## 3. Existing ontology foundation

`architecture/research-knowledge-ontology.v0.2.json` already contains the most important architectural separation.

It defines four layers:

### Epistemic

Represents what is observed, hypothesized, supported, rejected, unresolved, contradicted, or interpreted.

Authority: **NON_EXECUTABLE**

### Normative

Represents explicit reviewed constraints, gates, permissions, prohibitions, stopping rules, and reopening rules.

Authority: **SOURCE_DERIVED_ONLY**

### Execution

Represents what was actually implemented, validated, triggered, run, merged, produced, or received.

Authority: **OBSERVATIONAL**

### Decision bridge

Contains `CandidateAction` and `DecisionEvaluation`.

Critical existing rules:

```text
CandidateAction authority = NONE

DecisionEvaluation authority =
    EXTERNAL_POLICY_EVALUATOR_ONLY
```

and:

> No inferred/model-generated graph edge may create or widen a Permission, remove a Prohibition, satisfy a ReviewRequirement, or authorize executor action.

This authority firewall must survive the generalization unchanged.

The existing ontology also already provides:

- source precedence;
- exact provenance;
- contradiction preservation;
- supersession without history deletion;
- current-state projection;
- bounded query families;
- distinction between invalid execution and negative science;
- distinction between preregistered result and post-hoc interpretation.

The migration should extend this foundation rather than replace it.

---

## 4. Target architecture

The target system is a general durable semantic execution control plane.

```text
┌─────────────────────────────────────────────┐
│         WORKSPACE SEMANTIC GRAPH            │
│                                             │
│ research • tutoring • engineering • docs    │
│ presentations • planning • data science     │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
              COGNITIVE OPERATIONS
                       │
         deterministic / model / human
                       │
                       ▼
                 CandidateActions
                       │
                       ▼
┌─────────────────────────────────────────────┐
│       DETERMINISTIC AUTHORITY PLANE         │
│                                             │
│ policy • scope • provenance • dependencies  │
│ gates • permissions • prohibitions          │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
                EXECUTOR ROUTER
                       │
      capability + reasoning + context
      quota + cost + privacy + locality
                       │
        ┌────────┬─────┼─────┬──────────┐
        ▼        ▼     ▼     ▼          ▼
 deterministic Instant local hosted   frontier
                       │
                       ▼
┌─────────────────────────────────────────────┐
│        DURABLE EXECUTION KERNEL             │
│                                             │
│ claims • leases • attempts • async waits    │
│ retries • recovery • artifacts • receipts  │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
                RESULT / EVIDENCE
                       │
                       ▼
             VALIDATION / INTERPRETATION
                       │
                       └──────────────→ graph
```

The system must keep semantic/cognitive reasoning, authority, execution, and resource allocation separate.

---

## 5. Five-plane model

### 5.1 Semantic plane

Represents:

- goals;
- questions;
- requirements;
- evidence;
- findings;
- decisions;
- tasks/actions;
- artifacts;
- state and provenance.

It answers:

> What does the workspace currently mean?

### 5.2 Cognitive plane

Performs non-authoritative reasoning such as:

- decomposition;
- hypothesis generation;
- interpretation;
- synthesis;
- architecture design;
- lesson planning;
- argument construction;
- artifact critique;
- experiment design;
- candidate next-action generation.

It answers:

> What intellectual work should be considered next?

Its outputs are proposals, interpretations, or candidate actions.

### 5.3 Authority plane

Deterministically evaluates:

- permissions;
- prohibitions;
- scope;
- required reviews;
- provenance requirements;
- dependency gates;
- external consequence gates;
- project-owned policy.

It answers:

> What is actually allowed?

No cognitive executor may manufacture authority.

### 5.4 Execution plane

Owns:

- claims;
- leases;
- generation fencing;
- idempotency;
- attempts;
- retries;
- async waits;
- worker death;
- recovery;
- validation scheduling;
- receipts;
- artifact references.

It answers:

> What is actually running or completed?

### 5.5 Resource plane

Owns executor selection and scarcity accounting:

- provider;
- model;
- executor surface/harness;
- reasoning capability;
- tool capability;
- context capacity;
- locality;
- privacy;
- monetary cost;
- subscription allowance;
- token/compute quota;
- concurrency;
- current availability.

It answers:

> Which eligible executor should perform this work?

---

## 6. General semantic core

The ontology should become a general workspace semantic ontology with a small stable core.

Candidate common entities include:

```text
Intent
Goal
Question
Requirement
Constraint
Preference
Audience
Stakeholder

Source
Reference
Evidence
Observation
Finding
Claim
Decision
Alternative
Unknown

Plan
Workflow
Workstream
Task
Action
CandidateAction
Attempt
Result

Artifact
Deliverable
Revision
Review
Validation
AcceptanceCriterion
QualityCriterion

Dependency
Invariant
Risk
Permission
Prohibition
ReviewRequirement
AuthorityDecision

Capability
ReasoningRequirement
ContextRequirement
ResourceRequirement

Executor
ExecutorSurface
Provider
Model
Harness
Tool
QuotaPool
UsageRecord
```

The common core must remain deliberately smaller than the union of every domain.

---

## 7. Domain extensions

Domain-specific semantics extend the common core.

### Research extension

```text
ResearchProgram
ResearchQuestion
Hypothesis
Assumption
Experiment
ExperimentDesign
ScientificExecution
ScientificResult
Metric
Interpretation
BeliefUpdate
Residual
MechanismFamily
```

### Tutoring extension

```text
Course
Concept
Skill
Prerequisite
LearningObjective
MasteryState
LearningEvidence
Misconception
Exercise
Assessment
AssessmentItem
StudentAttempt
RetentionCheck
```

### Paper/publication extension

```text
Argument
Section
Citation
Figure
Table
ReviewerFinding
VenueConstraint
ReferenceRole
ExemplarHeuristic
PageBudget
```

### Presentation extension

```text
Presentation
Narrative
Slide
VisualAsset
SpeakerScript
AudienceTakeaway
Transition
LayoutConstraint
```

### Engineering extension

```text
Architecture
ArchitectureDecision
Component
Interface
Implementation
Test
Deployment
Runtime
Service
Incident
```

### Data-science extension

```text
Dataset
DataSlice
Feature
ModelFit
Evaluation
Metric
ErrorAnalysis
StatisticalAssumption
```

These lists are examples, not a closed universe.

---

## 8. Open-world extensibility contract

This is a hard architectural requirement.

Workspace Control is expected to gain new workflows and new domains over time.

The new execution kernel MUST NOT require a redesign every time a new workflow family appears.

### 8.1 No closed domain enum

The kernel must not contain logic equivalent to:

```python
if domain == "research":
    ...
elif domain == "tutoring":
    ...
elif domain == "slides":
    ...
```

for semantic behavior.

A new domain may register additional semantic types, relations, workflows, validators, artifact handlers, and capabilities without changing core scheduler semantics.

### 8.2 Stable core, extensible vocabulary

The ontology should have:

1. a small stable core namespace;
2. versioned domain-extension namespaces;
3. explicit registration/compatibility metadata.

Example:

```text
workspace:Artifact
workspace:Action
workspace:Evidence

research:Hypothesis
research:Experiment

tutor:Skill
tutor:MasteryState

publication:Section
publication:Citation

presentation:Slide
presentation:SpeakerScript
```

A future workflow can introduce, for example:

```text
grant:Proposal
grant:BudgetNarrative
grant:BroaderImpactClaim
```

without modifying the execution kernel.

### 8.3 Generic execution contracts

The execution kernel operates on generic contracts such as:

- dependencies;
- required capabilities;
- required reasoning class;
- context requirements;
- authority decision;
- artifact expectations;
- validation requirements;
- consequence class;
- retry/recovery semantics.

It should not need to know what a `Hypothesis`, `Slide`, or `MasteryState` means.

Domain adapters own that meaning.

### 8.4 Versioned workflow descriptors

New workflows should be introduced through versioned descriptors rather than new scheduler code where possible.

A workflow descriptor should be able to define:

- semantic owners;
- required inputs;
- stages;
- stage transition conditions;
- candidate-action templates or allowed action families;
- required capabilities;
- artifact/result roles;
- validation roles;
- authority/gate references;
- terminal conditions;
- allowed recursive expansion points.

### 8.5 Extension safety

A domain extension MUST NOT gain authority merely by defining a new node or relation.

Extensions may add:

- semantic vocabulary;
- derived epistemic relations;
- workflow templates;
- validation logic;
- executor capability declarations.

Extensions may not:

- create Permission;
- remove Prohibition;
- satisfy ReviewRequirement;
- widen an existing authority scope;
- bypass project-local source authority;
- cause an inferred semantic edge to become executable authority.

### 8.6 Compatibility and migration

Every extension should declare:

- extension identifier;
- schema/version;
- owning repository;
- compatible core version;
- source-of-truth boundary;
- migration behavior;
- validation contract.

Existing durable state must remain interpretable after extensions evolve.

### 8.7 Unknown workflows must fail structurally, not semantically hallucinate

If Workspace Control encounters a workflow or semantic extension it does not understand, it must not guess a mapping into an existing domain.

It should classify the workflow as unsupported/unresolved, preserve the source state, and require extension registration or an explicit compatible adapter.

---

## 9. Universal execution lifecycle

All domains should converge on a generic lifecycle.

```text
1. recover current durable semantic state
2. identify current objective/question/artifact requirement
3. produce or recover candidate work
4. evaluate dependencies and authority
5. classify reasoning/capability/context requirements
6. route to eligible executor
7. atomically claim work
8. execute bounded attempt
9. checkpoint on async/external wait
10. collect result/artifact/evidence
11. validate against domain-owned criteria
12. update semantic projection
13. decide:
      COMPLETE
      REVISE
      DECOMPOSE
      RETRY
      WAIT
      AUTHORITY_GATE
      ESCALATE_REASONING
      HUMAN_DECISION
14. continue until terminal objective state
```

The lifecycle is generic; domain-specific workflow descriptors define what the stages mean.

---

## 10. Executor model

The executor abstraction must separate model quality from execution surface.

```text
Provider
Model
ExecutorSurface
Harness
Toolset
CapabilityProfile
UsagePool
```

For example, the same nominal model used through two different harnesses is not necessarily the same executor capability.

Candidate executor classes include:

```text
DETERMINISTIC
CHATGPT_INSTANT
LOCAL_MODEL
FREE_HOSTED_MODEL
SUBSCRIPTION_AGENT
FRONTIER_CHATGPT
PAY_AS_YOU_GO_API
HUMAN
```

These are routing classes, not authority classes.

### Required executor metadata

At minimum:

```text
reasoning capability
coding capability
tool capability
GitHub capability
shell capability
web capability
artifact capability
multimodal capability
context capacity
privacy/locality
parallelism
availability
usage class
quota state
monetary cost
```

---

## 11. Scarce-usage optimization

The new system should optimize:

> useful verified progress per unit of scarce frontier allowance

rather than only minimizing monetary API cost.

### Resource classes may include

```text
SUBSCRIPTION_UNMETERED
SUBSCRIPTION_ALLOWANCE
PAY_AS_YOU_GO
LOCAL_COMPUTE
HUMAN_ATTENTION
```

### Usage metrics may include

```text
NONE
TOKEN_WEIGHTED
COMPUTE_WEIGHTED
MESSAGE_LIMIT
TIME_WINDOW
MONTHLY_CREDIT
GPU_TIME
```

### Routing preference

A typical capability ladder may be:

```text
DETERMINISTIC
→ INSTANT
→ LOCAL_MODEL
→ FREE/SUBSCRIPTION_HOSTED
→ FRONTIER_MODEL
→ PAY_AS_YOU_GO
```

but routing must not be a dumb fixed fallback chain.

The router must distinguish:

```text
TOO LARGE
→ decompose

INTRINSICALLY DIFFICULT
→ stronger reasoning
```

Importance alone must not force frontier reasoning.

### Context compression

Frontier executors should receive bounded semantic context packets rather than whole conversation histories.

A context packet should preferentially contain:

- current objective;
- relevant constraints/invariants;
- current findings;
- unresolved alternatives;
- exact evidence references;
- required output contract.

Raw evidence remains durably retrievable when needed.

### Semantic caching

High-value reasoning outputs should become durable reusable semantic objects such as:

- ArchitectureDecision;
- Finding;
- RejectedAlternative;
- Rationale;
- VerificationPlan;
- OpenQuestion.

Repeated downstream work should consume these objects rather than re-paying for the same reasoning.

---

## 12. Distributed execution evidence

Recent Instant-worker capability experiments established several execution properties that should inform the production design:

- conversation state must not be authoritative;
- fresh workers can reconstruct task state from durable GitHub evidence;
- action claims require atomic ownership;
- shared hot mutable queue branches become contention points;
- Git refs can act as distributed ownership/claim primitives;
- worker death requires lease/generation recovery;
- stale workers must fail closed;
- async validation/waits should consume no model reasoning;
- early workers may legitimately have stale global views;
- final global state must be reconstructable from durable evidence.

These experimental results are architecture evidence, not production authority.

The future execution kernel may reuse Git-ref primitives, PostgreSQL leasing, or another durable coordination substrate. Selection should be driven by the generic semantics rather than by attachment to the current prototype.

---

## 13. Domain truth remains local

Workspace Control must not absorb project-specific truth.

The ownership model remains:

```text
project-local domain authority
        ↓
shared semantic / behavioral contracts
        ↓
workspace coordination
        ↓
executor routing
        ↓
execution surface
```

Examples:

- PADataset remains authoritative for RF/DQNGuard science and experiment semantics.
- MTH602 remains authoritative for course, assignment, mastery, and report semantics.
- CIS560 and EAS501 remain authoritative for their course state.
- research-engine remains authoritative for its executable implementation and runtime behavior.
- workspace-control owns reusable cross-project orchestration, authority, portability, routing, and execution semantics.

The semantic graph is a provenance-preserving projection. It is not a replacement source of domain truth.

---

## 14. Migration strategy

The new system should be introduced incrementally.

### Phase A — inventory and formalize

Produce a workspace capability/workflow inventory mapping every existing workflow to:

- semantic entities;
- domain owner;
- authority source;
- execution primitives;
- executor capabilities;
- artifact types;
- validation requirements;
- async/external waits;
- consequence gates.

### Phase B — generalize ontology

Evolve the research knowledge ontology into the workspace semantic execution ontology while preserving:

- authority firewall;
- provenance;
- contradiction handling;
- supersession;
- bounded-query behavior.

### Phase C — generalize execution kernel

Extract the durable queue/worker/lease/retry behavior from research-engine into a domain-neutral execution model.

Do not remove research-engine-specific workflows until equivalent behavior is validated.

### Phase D — introduce heterogeneous executor routing

Add:

- capability profiles;
- reasoning requirement;
- context requirement;
- quota/cost state;
- executor surface/harness identity;
- routing decisions with explicit rationale.

### Phase E — migrate representative workflow families

At minimum validate:

1. coding + CI repair;
2. systems architecture/design review;
3. data-science experiment;
4. iterative scientific research;
5. paper creation/revision;
6. slide/presentation creation;
7. tutoring/study workflow;
8. homework/report production;
9. controller/runtime operation;
10. evidence-first architecture research.

### Phase F — desktop/interactive execution adapters

Only after the semantic and execution contracts stabilize should the Firefox/Instant worker console or equivalent interactive launch surfaces be frozen.

---

## 15. Acceptance requirements

The successor architecture is not accepted merely because it schedules tasks.

A representative end-to-end objective should demonstrate that the system can:

1. recover domain authority;
2. construct or update semantic state;
3. decompose work;
4. preserve candidate-action/authority separation;
5. route work by reasoning and capability requirements;
6. use deterministic/unmetered/local capacity before scarce frontier usage when sufficient;
7. execute and validate artifacts;
8. checkpoint external waits without burning model usage;
9. recover from worker failure;
10. preserve exact provenance;
11. update findings/decisions/mastery/artifact state correctly;
12. recursively revise or expand the work graph;
13. support domain-specific validation;
14. escalate only when lower tiers are insufficient;
15. complete without manual SHA/log/JSON transport;
16. expose frontier-allowance usage and routing decisions;
17. remain extensible to a previously unseen workflow family through a new domain/workflow adapter without kernel redesign.

---

## 16. Initial workstreams

The migration program should eventually contain workstreams equivalent to:

```text
A — workspace capability/workflow inventory
B — semantic ontology generalization
C — domain-extension/registration contract
D — authority projection
E — reasoning/capability/context model
F — usage-aware executor router
G — durable distributed execution kernel
H — claims/leases/recovery/generation fencing
I — result/evidence/artifact ingestion
J — recursive graph expansion/decomposition/escalation
K — context packet builder + semantic cache
L — executor adapters
M — existing workflow migration
N — desktop Instant-worker console
O — adversarial/end-to-end acceptance
```

The exact task decomposition should be created under normal Workspace Control authority rather than inferred as executable authority from this document.

---

## 17. Key invariants

The redesign must preserve these invariants:

1. **Semantic inference is never execution authority.**
2. **Project-local truth remains authoritative.**
3. **Every important semantic assertion retains provenance.**
4. **Contradictions are represented, not silently collapsed.**
5. **Execution success is not automatically artifact correctness.**
6. **Artifact correctness is not automatically semantic success such as mastery or scientific support.**
7. **External delivery/submission is distinct from internal completion.**
8. **Waiting consumes no reasoning executor.**
9. **Workers are disposable; durable state is authoritative.**
10. **Stale executors fail closed.**
11. **Frontier allowance is a managed resource, not the default execution substrate.**
12. **Large tasks are decomposed before stronger reasoning is selected.**
13. **Intrinsically difficult tasks may escalate to stronger reasoning.**
14. **Executor surface/harness is part of executor identity.**
15. **New workflow families must be addable without core-kernel redesign.**
16. **No domain extension may manufacture or widen authority.**
17. **Existing workflows must remain operable during migration until replacements are independently validated.**

---

## 18. Immediate next artifact

The next design artifact should be a **Workspace Capability & Workflow Inventory** derived from the actual repositories and existing workflows.

For each workflow, record:

```text
workflow_id
owning_repository
domain
intent/input
semantic entities
authoritative sources
candidate actions
authority/gates
executor capabilities
reasoning requirement classes
tools/surfaces
artifacts/results
validation
async waits
failure/recovery
external consequence
existing reusable contracts
migration target
```

This inventory should be evidence-driven from:

- `workspace-control`;
- `PADataset`;
- `research-engine`;
- `MTH602-AdamTrott`;
- `EAS501-AdamTrott`;
- `CIS560-AdamTrott`;

and expanded as future repositories/workflows enter the workspace.

The inventory itself should therefore also be open-world and versioned.

---

## 19. Design interpretation

The existing two months of Workspace Control work are not discarded.

They constitute:

- the behavioral specification;
- the authority model;
- the provenance model;
- the validated domain workflows;
- the execution/recovery prototypes;
- the artifact-production semantics;
- the tutoring semantics;
- the research methodology;
- the migration test corpus.

The next system should consolidate these abstractions into a common semantic execution architecture rather than replace them with another monolithic agent.

The desired result is a Workspace Control that can continue to grow in domains and workflows while preserving the same durable authority, provenance, validation, and autonomous iteration guarantees under changing model economics.
