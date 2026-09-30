# Course Workflows v2 Shared-Contract Review

Status: reviewed architecture input for `course-workflows-v2-refactor`

Architecture branch baseline entering review:
`workspace-control@8a6202b020d0733437960415f77833f2001da962`

This review is intentionally limited to reusable workspace-control behavior. It does
not migrate any course/application repository and does not change task-capsule v2
composition semantics.

## Evidence reviewed

Shared baseline:

- `policies/TUTORING_CONTRACT.md`
- `policies/OPERATOR_WORKFLOW.md`
- `policies/PORTABILITY_CONTRACT.md`
- `templates/COURSE_TUTOR_ADAPTER.md`
- `procedures/TUTOR_EVALUATION.md`

Pinned project evidence:

- MTH602-AdamTrott `62b7a03c7139cb3987b72ad66bdc532e8a61b82a`
  - `README.md`
  - `classnotes/CONTEXT.md`
  - `docs/sources/CONTEXT.md`
  - `study/TUTORING.md`
- CIS560-AdamTrott `tutor-framework@1af3ce7022d079b89f0fbca32f313a6853db1c60`
  - `README.md`
  - `experiments/README.md`
  - `experiments/WORKFLOWS.jsonl`
- EAS501-AdamTrott
  `eas501-tutor-bootstrap@aa6195377b856862124643d0fc501969467fad3b`
  - `README.md`
  - `COURSE_TUTOR.md`
  - `practice/exam01/CONTEXT.md`
- PADataset `resume-framework@078461795be3c1d3e5c3845c81607166fac9fad3`
  - `README.md`
  - `resumes/CONTEXT.md`
  - `resumes/applications/nreip2027/CONTEXT.md`

No project content was mutated.

## Findings

### 1. Preserve the current tutoring core

The shared tutoring contract already correctly owns the reusable
completion/mastery firewall, atomic skill diagnosis, evidence-grounded mastery,
persistence boundaries, direct-tool mutation semantics, and cold-start routing.
Those semantics should be extended rather than replaced.

Conversational "builder" and "tutor" instances are not architectural owners in
the shared contract today. There is therefore no shared conversational hierarchy
to delete. Project migrations should remove such dependencies only where a
project actually has them.

### 2. Add modality-aware source ingestion as reusable mechanics

MTH602 demonstrates a durable source model that is more general than its earlier
PDF/Mathpix path:

```text
original source evidence
-> modality-appropriate interpretation/transcription
-> reviewed semantic synthesis
-> deliberate promotion into course/study state
```

For classroom photographs and handwriting, direct multimodal interpretation is a
valid preferred path when it is more reliable than OCR. OCR/Mathpix remains
optional when it materially improves retrieval or transcription. Original images
remain source evidence and derived synthesis must preserve provenance,
uncertainty, ordering, and source kind.

This belongs in a shared ingestion procedure plus local adapter mappings, not in a
global course-source authority hierarchy.

### 3. Separate assessment authority from assessment relevance

The existing tutoring contract provides exam-readiness semantics but does not yet
model how a tutor decides which otherwise-authoritative material is most relevant
to a particular assessment.

Assessment relevance must be contextual evidence weighting, not a universal
source ranking. Relevant factors include:

- explicit current instructor assessment guidance;
- demonstrated correspondence to the announced problem form;
- current instructor specificity;
- recency;
- course/source role;
- coverage gaps and current mastery dependencies.

A prior exam, practice set, lecture example, review sheet, or homework may be
highly relevant in one context and secondary in another. Factual/course authority
and assessment relevance are separate axes.

### 4. Generalize document-artifact mechanics without moving domain truth

MTH602 report work and PADataset resume production independently demonstrate the
same reusable mechanical lifecycle:

```text
domain-owned content/requirements
-> source artifact
-> deterministic build/render
-> structural/static validation
-> rendered visual QA
-> bounded revision
-> delivery/submission gate
```

workspace-control may own this lifecycle and validation vocabulary. The owning
course/application/research repository continues to own content, formatting
requirements, facts, and submission semantics.

Visual QA is an artifact-validation operation. Automated visual inspection is
sufficient unless the owning workflow explicitly requires substantive human
judgment or approval. Human review must not be inserted merely because an older
workflow used it.

### 5. Add communications ingestion as a source adapter, not a new authority

CIS560 experiment B proved:

```text
forwarded Gmail source
-> normalized source-owned course facts + minimal provenance in Git
-> verified durable checkpoint
-> return to parent task from Git
```

Experiment C proved idempotent re-entry by exact source identity without rereading
Gmail or duplicating the durable record.

The shared architecture should therefore support communications ingestion with:

- source identity;
- sender/original sender when relevant;
- subject/time/provenance;
- normalized domain facts only;
- idempotent repository-first lookup;
- post-persistence return routing.

Forwarded Gmail is an available source adapter when school Outlook is
inaccessible. The architecture should not invent pseudo-real-time Outlook access.

### 6. Preserve single workflow binding in task-capsule v2

Task-capsule v2 should continue to bind at most one reusable workflow descriptor.
Composition belongs inside a descriptor through stages/procedure routing.

A course assessment task, for example, can bind one assessment-preparation
workflow whose stages invoke source-ingestion, study, and document-artifact
procedures. It must not gain an array of workflow bindings.

### 7. Existing active task pins remain compatibility boundaries

Shared changes produced by this refactor do not migrate existing tasks or project
locks automatically. Active tasks adopt a newer shared checkpoint only through an
explicit validated transition. Archived capsules remain immutable.

The active automated-research-engine task and archived PADataset integration task
are outside this architecture mutation.

## Smallest reusable shared changes

The implementation should be limited to:

1. extend `policies/TUTORING_CONTRACT.md` with:
   - assessment-authority versus assessment-relevance semantics;
   - modality-aware course-source ingestion boundary;
   - explicit automated-visual-QA default;
2. extend `templates/COURSE_TUTOR_ADAPTER.md` with local mappings for:
   - source ingestion/synthesis;
   - assessment scope/relevance evidence;
   - communications source ingestion;
   - document-artifact ownership/validation;
3. extend `procedures/TUTOR_EVALUATION.md` with regressions for:
   - multimodal classroom/handwritten ingestion;
   - contextual assessment relevance;
   - automated visual QA versus true human gates;
   - idempotent communications ingestion and parent return;
4. add reusable executor-neutral procedures for:
   - course source/content ingestion;
   - assessment preparation;
   - study-session execution;
   - assignment work;
   - communications ingestion;
   - document-artifact build/QA;
   - course bootstrap/migration;
5. add validated workflow descriptors for:
   - course bootstrap/migration;
   - content ingestion;
   - assessment preparation;
   - study session;
   - assignment work;
   - cheat-sheet build;
   - communications ingestion;
   - document-artifact build;
6. route the new shared workflow set from workspace-control documentation without
   changing project-local authority or task-capsule v2 schema.

## Explicit non-changes

This refactor must not:

- create a workspace-control-owned course fact hierarchy;
- make OCR/Mathpix mandatory for handwriting or classroom photographs;
- rank old exams above current practice material globally;
- require human visual approval for every rendered artifact;
- copy candidate/private application truth into workspace-control;
- move the PADataset resume domain automatically;
- mutate MTH602, CIS560, EAS501, or PADataset project content;
- alter existing project contract pins;
- alter archived task capsules;
- add multiple workflow bindings to task-capsule v2.

## Review result

PASS.

The evidence supports a bounded shared implementation. The next architecture
stage should define the workflow/procedure interfaces above, then implement and
validate them without project migration.
