# Workspace Capability & Workflow Inventory v0.1

Status: **DRAFT / NON-AUTHORITATIVE MIGRATION INVENTORY**

Parent design: `architecture/workspace-semantic-execution-migration.v0.1.md`

Branch: `workspace-semantic-execution-migration-v1`

## 1. Purpose

This inventory maps the major workflow families already present in the workspace to the semantic, authority, execution, artifact, validation, and executor capabilities that a successor Workspace Control architecture must preserve.

It is intentionally open-world.

The rows below are a current evidence sample, not a closed list of supported workflows. Future repositories and workflow families are expected to extend this inventory without requiring redesign of the generic execution kernel.

This inventory is not execution authority. It does not activate controllers, change project manifests, authorize Lambda mutation, cut over runners, or supersede project-local contracts.

---

## 2. Cross-cutting capability dimensions

Every workflow should eventually declare or derive the following dimensions:

| Dimension | Meaning |
| --- | --- |
| semantic owner | Repository/artifact that owns domain meaning |
| authoritative inputs | Exact sources that may establish facts/requirements |
| candidate work | Non-authoritative next actions or decompositions |
| authority/gates | Policy, scope, review, human, spend, or external consequence boundaries |
| reasoning requirement | None / bounded / moderate / intrinsically difficult / human judgment |
| executor capability | GitHub, shell, web, code, multimodal, artifact generation, local runtime, etc. |
| context requirement | Exact bounded semantic/provenance slice needed |
| execution semantics | Deterministic, interactive reasoning, local model, long-running job, external wait |
| artifacts/results | Durable outputs |
| validation | What proves completion/correctness |
| async waits | CI, experiment, rendering, external communication, human decision |
| recovery | Retry, resume, generation fencing, rollback, re-ingestion |
| consequence class | Internal reversible, external delivery, spend, live infrastructure, scientific trigger |
| usage class | Deterministic/local/unmetered/subscription/frontier/pay-as-you-go |
| migration status | Existing, partial, candidate, blocked, not yet represented |

---

## 3. Current workflow-family inventory

### 3.1 Scientific research and iterative experimentation

**Primary evidence owners**

- `adamtrott78/PADataset`
- `adamtrott78/research-engine`
- research-related workspace-control architecture/procedures

**Representative lifecycle**

```text
question
→ evidence/source acquisition
→ hypothesis / gap
→ experiment design
→ implementation
→ execution
→ result collection
→ interpretation
→ belief/finding update
→ next experiment
```

**Semantic entities**

- ResearchQuestion
- Hypothesis
- Assumption
- MechanismFamily
- ExperimentDesign
- ScientificExecution
- ScientificResult
- Evidence
- Finding
- Interpretation
- BeliefUpdate
- Residual
- CandidateAction

**Authority/gates**

- scientific/project-local truth remains local;
- model inference is non-authoritative;
- experiment trigger authority is distinct from experiment design/implementation authority;
- exact source/model/runtime bindings may be required;
- external scientific execution may require separate reviewed trigger authority.

**Executor capabilities**

- web/research discovery;
- PDF/document understanding;
- GitHub;
- code generation/review;
- shell/runtime;
- local model execution;
- GPU/CPU workload execution;
- experiment monitoring;
- statistical analysis.

**Validation**

- scientific/data contract;
- exact input/runtime/model provenance;
- result artifact integrity;
- statistical/result checks;
- distinction between invalid execution and negative science.

**Migration target**

Use the generic semantic graph + durable execution kernel while retaining research-engine/PADataset project-local truth and scientific contracts.

---

### 3.2 Software and systems engineering

**Primary evidence owners**

- `workspace-control`
- `research-engine`
- project repositories

**Representative lifecycle**

```text
objective
→ system inventory
→ architecture alternatives
→ design
→ implementation
→ tests
→ CI
→ diagnosis
→ repair
→ independent review
→ bounded activation/deployment
```

**Semantic entities**

- Requirement
- Constraint
- Architecture
- ArchitectureDecision
- Alternative
- Component
- Interface
- Implementation
- Test
- ValidationRun
- ReviewFinding
- Deployment
- Incident
- CandidateAction

**Authority/gates**

- design authority != implementation authority != live mutation authority;
- reviewed exact-head bindings;
- scope closure;
- validation tier;
- independent review where required;
- live infrastructure mutation requires exact authority;
- rollback semantics remain authoritative.

**Executor capabilities**

- GitHub read/write;
- code reasoning;
- test/CI inspection;
- shell/runtime when authorized;
- architecture synthesis;
- adversarial review.

**Migration target**

Generic engineering workflow descriptors over the same semantic/authority/execution substrate.

---

### 3.3 Repository-backed tutoring and coursework

**Primary evidence owners**

- `MTH602-AdamTrott`
- `EAS501-AdamTrott`
- `CIS560-AdamTrott`
- `workspace-control/policies/TUTORING_CONTRACT.md`

**Representative lifecycle**

```text
course authority + current student state
→ skill/dependency resolution
→ diagnosis
→ instruction / guided work / completion work
→ behavioral evidence
→ mastery update
→ assignment artifact
→ assessment preparation
→ later retention/transfer
```

**Semantic entities**

- Course
- Assignment
- Skill
- Prerequisite
- MasteryState
- Misconception
- LearningEvidence
- Exercise
- Assessment
- StudentAttempt
- Artifact
- SubmissionState

**Critical semantic firewalls**

```text
artifact correctness ≠ mastery
assignment completion ≠ mastery
source ingestion ≠ mastery
tutor-generated work ≠ student evidence
repository completion ≠ external submission
```

**Executor capabilities**

- multimodal source ingestion;
- mathematical reasoning;
- code execution;
- tutoring dialogue;
- assignment artifact production;
- GitHub persistence;
- PDF/document generation and QA.

**Migration target**

Tutoring remains a domain extension. Generic execution must not collapse mastery state into task-completion state.

---

### 3.4 Paper/publication production

**Primary evidence owner**

- `PADataset/papers/`

**Representative lifecycle**

```text
scientific ground truth
→ evidence map
→ claims / boundaries
→ draft
→ source/exemplar analysis
→ figure/table production
→ revision
→ reviewer audit
→ citation/reference checks
→ page-budget optimization
→ final build / visual QA
```

**Semantic entities**

- Claim
- Argument
- Section
- Citation
- ReferenceRole
- ExemplarHeuristic
- Figure
- Table
- ReviewerFinding
- VenueConstraint
- Revision
- ManuscriptArtifact

**Authority/gates**

- manuscript may not rewrite scientific truth for rhetorical convenience;
- citation/source provenance;
- page/layout pressure cannot invent or change facts;
- external submission is a separate consequence gate.

**Executor capabilities**

- synthesis/writing;
- literature analysis;
- LaTeX/build tooling;
- figure/table generation;
- PDF rendering;
- visual QA;
- citation checking.

**Migration target**

Publication workflow descriptor plus domain vocabulary over generic artifact/revision/validation primitives.

---

### 3.5 Presentation/slide production

**Primary evidence owner**

- `PADataset@milcom-presentation:presentations/milcom2026/`

**Representative lifecycle**

```text
audience + purpose
→ narrative
→ slide plan
→ evidence/claim selection
→ visual production
→ assembly
→ render
→ visual QA
→ script
→ presenter study material
→ revision
```

**Semantic entities**

- Presentation
- Audience
- Narrative
- Slide
- AudienceTakeaway
- Claim
- VisualAsset
- LayoutConstraint
- SpeakerScript
- Transition
- Preview
- DeckArtifact

**Authority/gates**

- presentation production must not invent scientific values;
- scientific/design claims remain owned by domain sources;
- rendering/layout is downstream of semantic authority;
- external presentation/upload remains distinct from build completion.

**Executor capabilities**

- narrative reasoning;
- image/visual production;
- PPTX/slide tooling;
- rendering;
- visual QA;
- scripting.

**Migration target**

Presentation extension + generic document/artifact lifecycle. Slide semantics must not be encoded in the execution kernel.

---

### 3.6 Generic document/report/cheat-sheet/resume production

**Primary evidence owner**

- `workspace-control/procedures/document_artifact_build.md`
- project-local artifact owners

**Generic lifecycle**

```text
domain contract
→ source preparation
→ deterministic build
→ structural/static validation
→ render
→ visual QA
→ bounded revision
→ delivery gate
```

**Semantic entities**

- DocumentArtifact
- Source
- Build
- Render
- QualityCriterion
- Validation
- Revision
- Delivery

**Migration target**

This is already close to a reusable generic workflow primitive and should be preserved nearly intact.

---

### 3.7 Evidence-first architecture/solution research

**Primary evidence owner**

- `workspace-control/procedures/evidence_first_solution_research.md`

**Lifecycle**

```text
problem framing
→ recover local evidence
→ external research
→ architecture-family synthesis
→ system-boundary review
→ bounded shortlist
→ benchmark/promotion contract
→ implementation handoff
```

**Important role in this migration**

The semantic-execution architecture itself should pass through this workflow before being treated as frozen.

The current candidate architecture is a **design hypothesis**, not an accepted conclusion.

Before foundational implementation, compare at least:

- evolve current Workspace Control with a new executor/resource layer only;
- generalize research-engine orchestration into a universal kernel;
- graph-first semantic execution architecture;
- event-sourced/durable workflow engine integration;
- hybrid architecture preserving existing task capsules + project workflows while adding semantic projection/router;
- any materially different architecture discovered by current external research.

The benchmark should measure migration complexity, authority preservation, extensibility, recovery semantics, token/allowance efficiency, context efficiency, workflow coverage, operational complexity, and rollback.

---

## 4. GitHub Actions / GitRunner control-plane migration integration

The existing GitRunner redesign is not replaced by the semantic-execution migration.

It is a partially completed infrastructure migration and must be carried forward as an explicit dependency/workstream.

### 4.1 Authoritative current task branch

Task:

`workspace-github-actions-control-plane-protocol-redesign-v1`

Branch:

`github-actions-control-plane-protocol-redesign-v1`

Task state observed on that branch:

```text
status = IN_PROGRESS
current_stage = bounded_migration_and_live_acceptance
```

The repository-only protocol architecture, typed compiler, compatibility verification, v3 implementation candidate, payload isolation, and first live v3 canary have already accumulated PASS evidence.

The migration must not restart those accepted phases merely because a broader Workspace Control redesign is underway.

### 4.2 Accepted first canary

The task records the first accepted v3 canary as:

```text
workspace-control-control-small-v1
```

The task explicitly says this canary must not be repeated merely to resume migration.

### 4.3 Remaining canary/migration order

The frozen migration plan currently orders:

```text
1. workspace-control-control-small-v1     accepted first canary
2. padataset-cpu-public-v1               next CPU-only class
3. padataset-gpu-single-public-v1        next GPU class
4. research-cpu-public-v1                separately gated
5. research-gpu-single-public-v1         NO_BY_DEFAULT
6. research-gpu-single-runtime-v1        NO_BY_DEFAULT
7. research-model-single-offline-v1      NO_BY_DEFAULT
8. research-model-dual-offline-v1        NO_BY_DEFAULT
9. research-model-dual-public-v1         NO_BY_DEFAULT
```

The Research GPU-derived classes inherit containment and must not become implicitly authorized by this migration plan.

### 4.4 PADataset current project routes

The GitRunner task branch already represents PADataset as an active registered project with:

```text
cpu-ci
  → cpu-public-ci-v1

gpu-ci
  → gpu-single-public-ci-v1
```

Both routes are owner/actor gated, require open same-repository PR heads, and forbid fork PR execution.

PADataset's public-repository threat boundary must remain explicit during migration.

### 4.5 Research Engine state

The GitRunner task branch contains a much larger Research Engine route set, including CPU validation and multiple GPU/model execution classes.

Some routes are represented as migration-live equivalents, while the GPU-derived classes remain containment-sensitive.

The semantic-execution migration must preserve this distinction:

```text
workflow represented
≠
class authorized for live activation
```

### 4.6 Workspace Shell dependency reconciliation

The GitRunner task's current `next_safe_action` states that live GitRunner mutation is paused until Workspace Shell ChatGPT acceptance completes, then calls for a fresh one-class canary/one-shot authority for `padataset-cpu-public-v1`.

That dependency has now been reconciled from durable GitHub evidence:

- PR #573 comment `6565110368` records **WORKSPACE SHELL V1 — LIVE CHATGPT ACCEPTANCE COMPLETE**;
- durable Workspace Shell head: `44b4e4f2020450c81cec56e86b711cdee7e651d9`;
- accepted installed execution/authority SHA: `01a95b61410e2f427b9885a19e6a0b9c5ee60a38`;
- Workspace Control Validation run `41359338969`: SUCCESS;
- current live `runtime_inventory` through the Workspace Shell connector returns normally with the expected mTLS/runtime socket structure.

The older `workspace-shell-mcp-v1` capsule still visible on `main` is therefore stale relative to the accepted PR-head state. This must be treated as a source-precedence example rather than evidence that acceptance is incomplete.

**Important authority boundary:** satisfying the Workspace Shell dependency does **not** authorize the next GitRunner canary. The controller task explicitly requires fresh exact one-class canary/one-shot authority for `padataset-cpu-public-v1`; Workspace Shell task authority must not be reused.

No live PADataset canary authority may be inferred from this inventory.

### 4.7 Integration with the new architecture

The GitRunner subsystem should become an execution-surface/provider under the future generic model, but its current migration must finish safely.

Conceptually:

```text
semantic action
→ authority decision
→ executor/resource routing
→ GitRunner execution request
→ typed controller/root protocol
→ JIT runner / payload broker
→ execution receipt
→ semantic result/evidence
```

The semantic layer must not bypass, duplicate, or reinterpret the typed GitRunner root authority protocol.

The current controller work therefore becomes both:

1. a production migration that still needs bounded completion; and
2. a proven execution-substrate implementation that the generalized architecture should reuse.

---

## 5. Asynchronous/resumable reasoning capability

A future executor substrate must support long-horizon cognitive work without requiring a long-lived model session.

Generic pattern:

```text
recover durable reasoning state
→ perform bounded reasoning quantum
→ checkpoint findings / questions / candidate actions
→ terminate invocation

external event or READY_CONTINUE
→ invoke compatible executor again
→ recover exact durable state
→ continue
```

Potential states:

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

This allows an executor such as ChatGPT Instant to participate in arbitrarily long workflows when the individual reasoning nodes remain within its capability.

Important limitation:

```text
more resumptions solve horizon/size
not intrinsic reasoning difficulty
```

Therefore routing should distinguish:

```text
TOO_LARGE
→ decompose and retry cheaper executor

INTRINSICALLY_DIFFICULT
→ escalate reasoning tier
```

This distinction should be empirically benchmarked rather than assumed.

---

## 6. Migration design uncertainty

The architecture described in the parent document is intentionally not frozen.

The current evidence supports several strong principles:

- durable state over conversational state;
- semantic reasoning separate from authority;
- project-local truth remains authoritative;
- execution/recovery must be deterministic;
- heterogeneous executor routing is required;
- frontier allowance must be treated as scarce;
- future workflows must be open-world extensions.

Those principles do **not** yet prove that one specific storage engine, graph representation, scheduler, orchestration kernel, or service decomposition is optimal.

Before implementation freeze, perform evidence-first comparison of architecture families and preserve the current system as the rollback/behavioral oracle.

The migration must therefore optimize for **reversible consolidation**, not a one-shot rewrite.

---

## 7. Initial migration matrix

| Workflow family | Existing owner | Existing reusable machinery | Main migration need |
| --- | --- | --- | --- |
| Research/experiments | PADataset + research-engine | provenance, jobs, leases, semantic execution, experiment workflows | general semantic/executor model |
| Engineering/coding | workspace-control + project repos | task capsules, operator workflow, CI/review | generic reasoning/action representation |
| Tutoring | course repos + tutoring contract | mastery/learning/domain adapters | ontology extension + generic execution |
| Papers | PADataset | evidence-grounded composition workflow | publication extension + artifact integration |
| Slides | PADataset | presentation plan/build/script/assets | presentation extension + artifact integration |
| Generic docs | workspace-control | document artifact procedure | direct reusable primitive |
| Architecture research | workspace-control | evidence-first solution research | use to validate this redesign |
| GitRunner/Lambda execution | workspace-control | typed v3 controller/root protocol | finish bounded fleet migration; expose as execution substrate |
| Local semantic models | research-engine | local routing/broker/runtime | integrate capability/resource router |
| Chat/Instant reasoning | benchmark branches + future adapter | durable-state recovery experiments | resumable reasoning executor + empirical capability map |

---

## 8. Immediate next work

Without live infrastructure mutation:

1. expand this inventory from repository evidence;
2. map concrete workflow descriptors and task capsules to generic semantic/execution primitives;
3. reconcile the GitRunner migration's exact current durable state and remaining gates;
4. conduct evidence-first architecture-family comparison before freezing the successor design;
5. define benchmark cases that include:
   - research;
   - paper production;
   - presentation production;
   - tutoring;
   - homework/report production;
   - coding + CI repair;
   - architecture review;
   - data science;
   - GitRunner/controller operations;
   - future/unseen workflow extension;
6. define an Instant-vs-frontier resumable-reasoning experiment to measure where decomposition preserves effectiveness and where escalation is required.

No live Lambda or project-controller mutation is authorized by this inventory.
