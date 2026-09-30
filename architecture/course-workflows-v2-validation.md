# Course Workflows v2 Shared Validation

Status: **PASS**

Implementation under test:

`workspace-control@f5d7a1a97a135cc4e238119789cda4aed773ae9b`

Validation surface: repository-read regression over the immutable shared
implementation plus the pinned project evidence named by the parent task.

This validation does not migrate or mutate MTH602, CIS560, EAS501, or PADataset.

## 1. Implementation-scope regression — PASS

The implementation checkpoint is exactly one commit ahead of the validated
workflow-design checkpoint
`da4ddc9aaca4cb18d6dbe70b089189fd6a1d18be`.

The implementation commit changes exactly:

- root README routing;
- `policies/TUTORING_CONTRACT.md`;
- `templates/COURSE_TUTOR_ADAPTER.md`;
- `procedures/TUTOR_EVALUATION.md`;
- seven new shared procedures;
- eight new workflow descriptors.

The workflow-descriptor schema remains blob
`8bcbe00d83f644d705adbe2a57749a9466ca1260`.

Task-capsule v2 remains blob
`3c6c424d2a087857a9d59fec2abb6732afe6d132`.

The archived PADataset integration capsule and the active automated-research-
engine task were not changed by the architecture implementation.

## 2. Descriptor structure and exact durable identity — PASS

All eight descriptors were read from the immutable implementation checkpoint.
Every descriptor:

- has `schema_version: 1`;
- is owned by registered repository `workspace-control`;
- has an existing committed `owner.context_path`;
- has only safe workspace-control-relative owner/route paths;
- has unique ordered stage IDs;
- references only earlier stage dependencies;
- contains a nonempty validation contract per stage;
- contains no task live-state fields;
- encodes no target-project artifact paths;
- has a committed content identity.

Durable descriptor identities:

| Descriptor | Content blob |
|---|---|
| course bootstrap/migration | `da6076a9b4baf328d6a91526f6dff7aa999733b6` |
| course content ingestion | `4c9037d7d5fc0937ae2193684566c9875ae6cde7` |
| course assessment preparation | `a576677dc886bd70826789b37dcce2499190c2f1` |
| course study session | `1a28468d3cc35243273a21ca12e10c1f7c404c67` |
| course assignment work | `8a0f596add333737e03c72a81e71a7eb075b53fc` |
| course cheat-sheet build | `14a13e820b5b106e55e7bbbcc252e67abcb47351` |
| course communications ingestion | `ebb5fe64b36709d8cf6b17059df2ed1916494cf5` |
| document-artifact build | `0d66b919acdd2e51c08d2e8496c41dc22aed47c4` |

The implementation tree contains every descriptor owner and every entry-route
path. No descriptor route is dangling.

## 3. Cold-start routing and project-authority boundary — PASS

The root README now identifies `workflows/` as the reusable course/document
workflow surface and states the one-binding composition rule.

A cold reader can follow:

```text
workspace-control README
-> one workflow descriptor
-> shared procedure/policy entry route
-> concrete task capsule + target project root/local adapter
-> project-owned authority/artifacts
```

The shared descriptors deliberately leave project-specific
`expected_artifacts` empty. Concrete project artifact paths and mutation scope
must come from the task capsule and project owner.

This prevents workspace-control from becoming a hidden course/application truth
repository.

## 4. Task-capsule single-workflow compatibility — PASS

At the implementation checkpoint, task-capsule v2 defines `workflow` as
object-or-null through `$defs.workflow_identity`.

It is not an array.

The required binding identity remains:

- repository;
- descriptor path;
- exact checkpoint SHA.

Conceptual composition is therefore expressed by descriptor stages/procedure
routes without changing task-capsule v2.

## 5. Multimodal source-ingestion regression — PASS

Shared evidence:

- `procedures/course_content_ingestion.md` blob
  `2168f10be71b6045cabac1f329ec0b527c981381`;
- updated tutoring contract blob
  `c6eb14abeb35d7e60a46fc02f29a70b5cc23ab1c`.

The shared route preserves original evidence, allows direct multimodal
interpretation for readable classroom/handwritten material, uses OCR/Mathpix only
when it materially improves the task, requires native-source verification when a
derivative is ambiguous, and keeps uncertainty explicit.

Pinned MTH602 evidence:

`MTH602-AdamTrott@62b7a03c7139cb3987b72ad66bdc532e8a61b82a`

`classnotes/CONTEXT.md` blob
`51fa55527656da20312582c68306e5320f4515b5` states that original classroom
visual evidence is the primary source layer, direct visual synthesis is preferred
when OCR adds little value or performs poorly, and transcription is optional.

The shared contract therefore generalizes demonstrated behavior without making
Mathpix mandatory.

## 6. Assessment-relevance regression — PASS

Shared procedure:

`procedures/course_assessment_preparation.md` blob
`f8ae57b6a595659655396d6d77c5442d5f640792`.

It keeps course/source authority separate from assessment relevance and uses
contextual factors including explicit current instructor guidance,
problem-form correspondence, instructor specificity, recency, source role,
coverage gaps, and mastery dependencies.

It explicitly rejects a universal ordering among old exams, practice sets,
homework, lecture examples, and review sheets.

Pinned EAS501 evidence:

`EAS501-AdamTrott:eas501-tutor-bootstrap@aa6195377b856862124643d0fc501969467fad3b`

`practice/exam01/CONTEXT.md` blob
`d780a6a58c3a1244af3136e079078acedcefb7f0` defines Exam 1 evidence as the
instructor-specified practice set plus current course material and requires
native-source verification for known OCR ambiguity.

The cheat-sheet descriptor composes assessment selection and document-artifact
mechanics internally through eight ordered stages; no second task workflow
binding is needed.

## 7. Document-artifact / LaTeX / visual-QA regression — PASS

Shared procedure:

`procedures/document_artifact_build.md` blob
`fde47bd4596e02dcf9e980c52bf46d95161b8349`.

It defines:

```text
domain-owned requirements/content
-> source
-> deterministic build
-> structural/static validation
-> render
-> visual QA
-> bounded revision
-> delivery gate
```

Automated rendered inspection is sufficient unless the owning project explicitly
requires substantive human judgment. External delivery remains a separate
consequence gate.

Pinned MTH602 evidence demonstrates the LaTeX case:

- `homework/hw01/CONTEXT.md` blob
  `0a0c380c8d6abcd006c3a81fa80e4e0a45f0b425`;
- mathematical work belongs in `report/main.tex`;
- the report source success check is a clean LaTeX compile;
- the final `report/HW1_AdamTrott.pdf` success check includes rendered visual
  review.

Pinned PADataset resume evidence demonstrates the production-spec/revision case:

`PADataset:resume-framework@078461795be3c1d3e5c3845c81607166fac9fad3`

`resumes/CONTEXT.md` blob
`8c4ad1e2f30fc7f647f696990024d5dce1d81f9f` records semantic + visual QA and
bounded revision, including explicit page-budget revision after the first render
without silently changing locked resume claims.

The shared procedure captures the reusable mechanics while leaving both domains'
content authority local.

## 8. Communications-ingestion/idempotency regression — PASS

Shared procedure:

`procedures/course_communications_ingestion.md` blob
`2be9899bcef29fabfef9b32c03e2a1c555e2a37d`.

Shared descriptor:

`workflows/course-communications-ingestion.v1.json` blob
`ebb5fe64b36709d8cf6b17059df2ed1916494cf5` with idempotency identity
`source-identity`.

The route performs repository-first lookup, reads an authorized message only when
durable state is insufficient, persists normalized domain facts plus minimal
provenance, verifies the project checkpoint, and returns to the parent task from
durable state.

Pinned CIS560 evidence:

`CIS560-AdamTrott:tutor-framework@1af3ce7022d079b89f0fbca32f313a6853db1c60`

`experiments/WORKFLOWS.jsonl` blob
`f6a273963191f1904209c9833a6d8acce0d06402` records:

- experiment B: forwarded Gmail source
  `gmail:1a0d08b2196e8a4a` persisted to Git and parent return from durable state;
- experiment C: repository-first exact-identity re-entry, no Gmail full-body
  reread, no duplicate record, and no source-state mutation.

The shared route generalizes demonstrated behavior and does not invent direct
Outlook connectivity.

## 9. Continuation and gate regression — PASS

`policies/OPERATOR_WORKFLOW.md` remains the exact baseline blob
`32a0d46c0269fec0f84dadf62427e53adeb95418`.

Its continuation obligation requires an authorized executor to continue while a
safe in-scope surface exists and rejects chat turns, commit boundaries,
successful substages, and convenient stopping points as suspension boundaries.

Across all eight new descriptors:

- there is no unconditional human-review gate;
- project mutation authority is explicit where needed;
- runtime is conditional only where an actual build/runtime is needed;
- external-delivery approval appears only on artifact workflows where an
  externally consequential action may occur.

This is compatible with automated visual QA and the continuation obligation.

## 10. Executor handoff / durable recovery regression — PASS

The handoff contract remains:

```text
workspace-control root
-> task capsule
-> one exact workflow binding when used
-> descriptor at exact checkpoint/content
-> target project owner/evidence
```

The workflow schema, task schema, and operator contract are unchanged by this
implementation. Every new descriptor has an immutable path/checkpoint/blob
identity suitable for a future child task capsule.

No conversation-specific builder/tutor role is needed for recovery.

## Runtime-validation boundary

No shared executable source, validator code, or schema was changed by this
implementation. The new architecture is declarative policy/procedure/descriptor
content, and the parent task explicitly selected repository-read validation.

Accordingly, this stage validates the shared mechanics against immutable real
project evidence rather than fabricating a workspace-control-owned course build.

Project-specific runtime/build validation belongs to each child migration task
after it explicitly adopts the promoted shared checkpoint.

## Validation result

All required shared regressions pass.

The architecture is ready for explicit reviewed promotion to workspace-control
`main`. Project migrations remain separate child tasks.
