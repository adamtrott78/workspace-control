# Course Workflows v2 Descriptor and Procedure Design

Status: reviewed design for `course-workflows-v2-refactor`

Design baseline:
`workspace-control@0624110cf808951b65f01c4851f90a3178988237`

The design uses the existing workflow-descriptor v1 contract unchanged.

Relevant existing owners:

- `schemas/workflow_descriptor.v1.schema.json`
- `procedures/workflow_descriptor.md`
- `templates/workflow_descriptor.v1.json`
- `policies/TUTORING_CONTRACT.md`
- `policies/OPERATOR_WORKFLOW.md`
- `policies/PORTABILITY_CONTRACT.md`

## Design rules

### One reusable workflow binding per task

A task-capsule v2 execution may bind one exact workflow descriptor. Conceptual
composition is expressed inside that descriptor through ordered stages and routes
to shared procedures.

No workflow-array or multi-binding extension is introduced.

### Workspace-control owns mechanics, not domain truth

The descriptors below are legitimately workspace-control-owned because they
define reusable coordination/tutoring/artifact mechanics.

At execution time, every procedure MUST route to the target project's local
owner for:

- course/application facts;
- assignment or assessment requirements;
- source authority;
- notation;
- candidate facts;
- project artifact semantics;
- project-specific deterministic commands;
- submission/delivery rules.

The workspace-control descriptor therefore does not encode target-project paths
as if they were workspace-control authority paths.

### Descriptor path fields remain workspace-control-relative

For these shared descriptors:

- `owner.context_path` is the shared procedure owning the reusable mechanics;
- `entry_route` contains workspace-control shared procedures/policies;
- `authority_owners` names only workspace-control shared owners;
- project-local authority is a required runtime input resolved by the procedure;
- `expected_artifacts` stays empty when the output path is project-owned and
  varies by integration;
- `artifact_lifecycle` stays empty in v1 unless a stable workspace-level
  lifecycle object is genuinely needed;
- project mutation scope comes from the concrete task capsule/project adapter,
  not from invented cross-repository glob paths in the descriptor.

This preserves descriptor-v1 repository-relative path semantics.

## Shared procedure interfaces

The implementation will add seven executor-neutral procedures.

### 1. `procedures/course_bootstrap_migration.md`

Purpose: integrate an existing or new course repository with the pinned shared
architecture without rewriting course truth.

Required runtime inputs:

- exact target repository/checkpoint;
- project root route;
- current compatible shared-contract pin, if any;
- project-local course/source/tutoring/artifact owners;
- authorized mutation scope.

Stages owned by the procedure:

1. inspect exact target state and current compatibility pin;
2. recover existing local owners and preserve valid project semantics;
3. map only missing local adapter roles;
4. bind the selected shared checkpoint explicitly;
5. validate cold-start routing and mutation boundaries;
6. checkpoint the project migration.

Hard requirements:

- no silent contract migration;
- no deletion of valid project-local history merely to match a template;
- no builder/tutor conversational hierarchy requirement;
- project migration occurs only in its own migration task/capsule.

### 2. `procedures/course_content_ingestion.md`

Purpose: preserve source evidence and produce a provenance-aware semantic
representation using the modality that best fits the source.

Required runtime inputs:

- owning project source-ingestion context;
- exact source identity/provenance;
- source bytes or authorized source surface;
- intended promotion target, if any.

Canonical mechanics:

```text
identify source
-> preserve original evidence
-> choose modality-appropriate interpretation
-> synthesize/review
-> validate provenance + uncertainty
-> deliberately promote into project-owned semantic state
```

Rules:

- original images/PDFs/messages remain source evidence;
- direct multimodal interpretation is preferred for readable classroom/
  handwritten images when OCR is not useful;
- OCR/Mathpix is optional and must never silently replace original visual
  authority;
- derived synthesis records uncertainty and source kind;
- repeated source identities should be idempotent where the local project
  provides a durable lookup key.

### 3. `procedures/course_assessment_preparation.md`

Purpose: turn assessment scope, relevance evidence, mastery state, and source
authority into a prioritized preparation plan/execution loop.

Required runtime inputs:

- project-local assessment owner/scope;
- current mastery/skill graph;
- current instructor guidance;
- relevant course/source owners.

Assessment relevance is contextual evidence weighting, not authority ranking.

Factors may include:

- explicit current instructor assessment guidance;
- demonstrated problem-form correspondence;
- current instructor specificity;
- recency;
- source role;
- coverage gaps;
- prerequisite/mastery dependencies.

The procedure must never encode a universal ordering such as
`prior exam > practice set`.

### 4. `procedures/course_study_session.md`

Purpose: execute one repository-backed learning/study session using durable
mastery semantics.

Canonical loop:

```text
recover scope + mastery
-> diagnose earliest useful dependency
-> teach smallest missing unit
-> return control
-> require application/transfer
-> persist evidence at meaningful boundary
```

The completion/mastery firewall remains authoritative. Tutor-generated work does
not become student mastery evidence.

### 5. `procedures/course_assignment_work.md`

Purpose: coordinate learning, completion, code/report production, and persistence
for an assignment while preserving the distinction between artifact completion
and mastery.

The procedure:

- loads the project assignment owner first;
- selects LEARNING/COMPLETION/MASTERY_RECOVERY semantics from the shared tutoring
  contract based on user intent and durable state;
- routes document/code artifact work to its owning project context;
- invokes the shared document-artifact mechanics when applicable;
- persists learning/mastery evidence separately from completion state;
- respects external submission as a project/user gate.

### 6. `procedures/course_communications_ingestion.md`

Purpose: ingest domain-relevant communications into durable project state without
making the communication surface a permanent authority.

Canonical mechanics:

```text
repository-first lookup by source identity
-> if absent, read authorized communication source
-> normalize only domain-owned facts + minimal provenance
-> persist through project owner
-> verify durable checkpoint
-> return to parent task from durable project state
```

Requirements:

- exact source identity when available;
- idempotent re-entry;
- forwarded Gmail is a valid adapter when the original school Outlook surface is
  unavailable;
- no invented pseudo-real-time Outlook dependency;
- message sending is not implied by read/ingest authority.

### 7. `procedures/document_artifact_build.md`

Purpose: provide domain-neutral mechanics for reproducible document artifacts
such as homework reports, cheat sheets, resumes, and similar deliverables.

Canonical lifecycle:

```text
domain-owned requirements/content
-> source artifact
-> deterministic build/render
-> structural/static validation
-> rendered visual QA
-> bounded revision
-> delivery/submission gate
```

Rules:

- domain content and formatting requirements remain project-owned;
- process exit alone is insufficient;
- rendered visual QA is a validation operation;
- automated visual QA is sufficient by default;
- substantive human judgment is required only when the owning workflow makes it
  authoritative;
- external delivery/submission remains a consequence gate when required.

## Workflow descriptor set

Implementation will create `workflows/` with eight descriptors.

### A. `workflows/course-bootstrap-migration.v1.json`

Workflow ID: `course-bootstrap-migration-v1`

Owner context:
`procedures/course_bootstrap_migration.md`

Stages:

1. `inspect-target`
2. `recover-local-owners`
3. `map-shared-contract`
4. `validate-cold-start`
5. `checkpoint-migration`

The workflow never performs project migration merely because the descriptor is
loaded; the concrete task capsule supplies repository mutation authority.

### B. `workflows/course-content-ingestion.v1.json`

Workflow ID: `course-content-ingestion-v1`

Owner context:
`procedures/course_content_ingestion.md`

Stages:

1. `resolve-source`
2. `preserve-original`
3. `interpret-modality`
4. `synthesize`
5. `validate-provenance`
6. `promote-project-state`

Capability classes may include repository read/write, source retrieval, and
multimodal vision/OCR when actually needed. No one modality is mandatory.

Idempotency identity:
`source-identity`

### C. `workflows/course-assessment-preparation.v1.json`

Workflow ID: `course-assessment-preparation-v1`

Owner context:
`procedures/course_assessment_preparation.md`

Stages:

1. `recover-assessment-scope`
2. `collect-relevance-evidence`
3. `map-skill-state`
4. `prioritize-preparation`
5. `execute-preparation`
6. `validate-readiness-state`

This workflow may route subordinate study/artifact mechanics through procedure
entry routes while remaining the task's single reusable workflow binding.

### D. `workflows/course-study-session.v1.json`

Workflow ID: `course-study-session-v1`

Owner context:
`procedures/course_study_session.md`

Stages:

1. `recover-learning-state`
2. `diagnose`
3. `remediate`
4. `transfer-check`
5. `persist-evidence`

### E. `workflows/course-assignment-work.v1.json`

Workflow ID: `course-assignment-work-v1`

Owner context:
`procedures/course_assignment_work.md`

Stages:

1. `load-assignment-owner`
2. `recover-learning-completion-state`
3. `execute-assignment-work`
4. `build-required-artifacts`
5. `persist-learning-state`
6. `validate-assignment-state`

### F. `workflows/course-cheat-sheet-build.v1.json`

Workflow ID: `course-cheat-sheet-build-v1`

Owner context:
`procedures/course_assessment_preparation.md`

Entry route additionally includes:
`procedures/document_artifact_build.md`

Stages:

1. `recover-assessment-scope`
2. `select-high-value-content`
3. `compose-source`
4. `build-render`
5. `structural-validation`
6. `visual-qa`
7. `bounded-revision`
8. `delivery-gate`

Content selection uses assessment-relevance evidence plus mastery/coverage gaps;
it is not a global source ranking.

### G. `workflows/course-communications-ingestion.v1.json`

Workflow ID: `course-communications-ingestion-v1`

Owner context:
`procedures/course_communications_ingestion.md`

Stages:

1. `repository-first-lookup`
2. `retrieve-source-if-needed`
3. `normalize-domain-facts`
4. `persist-project-state`
5. `verify-checkpoint`
6. `return-to-parent`

Idempotency identity:
`source-identity`

### H. `workflows/document-artifact-build.v1.json`

Workflow ID: `document-artifact-build-v1`

Owner context:
`procedures/document_artifact_build.md`

Stages:

1. `load-domain-contract`
2. `prepare-source`
3. `build`
4. `structural-validation`
5. `render`
6. `visual-qa`
7. `bounded-revision`
8. `delivery-gate`

The delivery gate may be empty for an internal artifact. Human judgment is a gate
only when declared by the owning project/workflow.

## Descriptor-v1 compatibility check

The proposed descriptors fit the current v1 validator without schema changes:

| v1 field | Design use |
|---|---|
| `schema_version` | always `1` |
| `workflow_id` | stable IDs above |
| `owner.repository` | `workspace-control` |
| `owner.context_path` | one of the seven shared procedure paths |
| `entry_route` | shared procedure/policy paths only |
| `stages[].id` | ordered unique IDs above |
| `stages[].depends_on` | references only earlier stages |
| `stages[].execution_owner` | reusable semantic execution owner, never a chat instance |
| `stages[].authority_owners` | shared workspace-control owners only |
| `stages[].required_capabilities` | capability classes, not hard-coded executors |
| `stages[].deterministic_entrypoint` | `null` unless workspace-control genuinely owns an executable entrypoint |
| `stages[].expected_artifacts` | empty for project-owned variable artifact paths |
| `stages[].artifact_lifecycle` | empty in v1 unless a stable shared declaration is necessary |
| `stages[].validation` | nonempty semantic validation requirements |
| `stages[].gates` | only genuine capability/judgment/consequence gates |
| `stages[].forbidden_mutations` | empty unless the restriction is meaningful in the descriptor owner repository |
| `forbidden_mutations` | empty; concrete project/task scope remains authoritative |
| `idempotency_identity` | null except source-identity workflows |

No proposed descriptor requires:

- multiple task workflow bindings;
- new live-state fields;
- cross-repository absolute paths;
- task state inside a descriptor;
- a workflow-descriptor schema change.

## Validation plan

During implementation:

1. create all seven procedure owners first;
2. create all eight descriptors against those existing owner paths;
3. ensure every descriptor is tracked in the same workspace-control commit or a
   later descendant;
4. run/replicate the existing v1 structural checks;
5. validate exact durable binding after commit;
6. test task-capsule v2 with one descriptor binding only;
7. perform cold-start/regression validation before promotion.

## Design result

PASS.

The existing workflow-descriptor v1 contract is sufficient for the required
course/application shared mechanics. No schema mutation is justified.
