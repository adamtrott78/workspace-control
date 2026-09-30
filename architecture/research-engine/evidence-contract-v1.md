# Research Engine Evidence Contract v1

Status: DRAFT CONTRACT
Parent architecture: ../automated-research-engine-v1.md
Created: 2026-09-30

## 1. Purpose

This contract defines what the automated research engine must preserve before it
can safely claim to have learned scientific knowledge from a paper.

The contract is intentionally storage-agnostic.

It does not choose:

- relational versus graph persistence;
- vector database;
- event store;
- embedding model;
- PDF parser;
- LLM;
- retrieval framework.

Those are implementation choices.

This contract defines the information those implementations must be able to
represent without loss.

## 2. Core assertion

The engine may say:

> "Evidence supports scientific statement S."

only when it can produce a durable provenance path from S to source material and
the experimental context required to interpret that material.

The minimum conceptual path is:

```text
Statement / Claim
  -> EvidenceRelation
  -> source Claim and/or Result
  -> Experiment / Method / Dataset / Metric context
  -> WorkVersion
  -> SourceArtifact
  -> SourceLocator
```

Not every paper exposes every node cleanly. Missing context must be represented as
missing or unresolved, never invented.

## 3. Record classes

The v1 contract defines these core record classes:

1. Work
2. WorkVersion
3. SourceArtifact
4. SourceLocator
5. DiscoveryRun
6. CorpusDecision
7. EvidenceObject
8. Claim
9. Method
10. Experiment
11. DatasetOrPopulation
12. Metric
13. Result
14. Limitation
15. Inference
16. EvidenceRelation
17. VerificationEvent
18. SynthesisArtifact

Additional domain-specific types may extend these records without weakening the
base provenance requirements.

## 4. Identity rules

### 4.1 Engine identity is distinct from external identity

External identifiers are attributes, not the only primary identity.

Examples:

- DOI;
- OpenAlex work ID;
- Semantic Scholar paper ID;
- PMID/PMCID;
- arXiv ID;
- publisher identifier;
- repository identifier.

The engine assigns a stable internal identity so that:

- one conceptual work can have multiple external identifiers;
- one work can have multiple versions;
- an identifier correction does not require replacing downstream evidence IDs.

### 4.2 Work versus WorkVersion

A Work represents the conceptual scholarly work.

A WorkVersion represents a specific version, such as:

- submitted preprint;
- revised preprint;
- accepted manuscript;
- version of record;
- corrected version.

Evidence is always sourced from a WorkVersion, not from an abstract Work.

### 4.3 SourceArtifact is content-addressed where bytes are available

For acquired immutable content, SourceArtifact should use or include a
cryptographic content digest such as SHA-256.

This permits the engine to distinguish:

- two URLs serving identical bytes;
- a changed file at the same URL;
- multiple artifacts for the same WorkVersion.

## 5. Work

Minimum fields:

```text
work_id
title
canonical_title
work_type
publication_date
venue
authors[]
external_ids{}
language
retraction_status
correction_status
created_at
updated_at
```

Important rules:

- bibliographic metadata may be corrected over time;
- source/provider provenance for metadata should be retained;
- retraction/correction status must propagate to downstream synthesis warnings;
- title similarity alone must not automatically merge works.

## 6. WorkVersion

Minimum fields:

```text
work_version_id
work_id
version_type
version_label
publication_or_posting_date
external_ids{}
source_provider
license_if_known
is_version_of_record
supersedes_version_id | null
created_at
```

The engine must preserve which version an evidence object came from.

## 7. SourceArtifact

A SourceArtifact represents acquired source content.

Minimum fields:

```text
artifact_id
work_version_id
content_hash
hash_algorithm
media_type
format
byte_size | null
acquisition_method
provider
source_uri_or_identifier
access_class
license_if_known
retrieved_at
parser_state
```

Suggested access classes:

- OPEN_ACCESS
- REPOSITORY_COPY
- LICENSED_ACCESS
- USER_SUPPLIED
- METADATA_ONLY
- ABSTRACT_ONLY
- ACCESS_REQUIRED
- ACQUISITION_FAILED

Artifact bytes and access rights are distinct concepts. The engine may know that
an artifact exists without being allowed to retain or redistribute it.

## 8. SourceLocator

SourceLocator anchors extracted evidence to the source artifact.

Minimum fields:

```text
locator_id
artifact_id
locator_quality
section_path[]
page_number | null
paragraph_index | null
normalized_text_start | null
normalized_text_end | null
xml_path | null
pdf_bbox | null
table_id | null
figure_id | null
caption_id | null
raw_anchor | null
```

Locator quality:

- EXACT
- STRUCTURAL
- APPROXIMATE
- UNAVAILABLE

Rules:

- never claim exact page/span precision when the parser cannot support it;
- preserve both logical structure and physical page anchors when available;
- table/figure-derived evidence should identify the table/figure explicitly;
- normalized-text offsets must identify the exact normalized artifact version.

## 9. DiscoveryRun

A DiscoveryRun makes corpus construction reproducible.

Minimum fields:

```text
discovery_run_id
research_scope_id
provider
adapter_version
query
structured_parameters
filters
sort
started_at
completed_at
raw_response_hash_or_artifact
result_work_ids[]
parent_discovery_run_id | null
expansion_type | null
```

Expansion types may include:

- QUERY
- REFERENCES
- CITATIONS
- RELATED_WORKS
- AUTHOR
- VENUE
- KEYWORD_REFINEMENT
- NOVELTY_CHALLENGE

The system should be able to answer why a paper entered the candidate corpus.

## 10. CorpusDecision

A CorpusDecision records screening state.

Minimum fields:

```text
decision_id
work_id
research_scope_id
decision
reason_codes[]
rationale
decider_type
decider_identity
evidence_available
decided_at
supersedes_decision_id | null
```

Suggested decisions:

- INCLUDE_DEEP_READ
- INCLUDE_METADATA_ONLY
- DEFER
- EXCLUDE_IRRELEVANT
- EXCLUDE_DUPLICATE
- EXCLUDE_WRONG_VERSION
- EXCLUDE_SCOPE
- EXCLUDE_ACCESS_LIMITATION

Screening decisions are versioned. They are not silently overwritten.

## 11. EvidenceObject base contract

Every scientific extraction derives from EvidenceObject.

Minimum fields:

```text
evidence_id
evidence_type
work_id
work_version_id
artifact_id
locator_id | null
raw_source_form | null
normalized_form
extraction_run_id
extractor_type
extractor_identity
extractor_version
extracted_at
confidence | null
verification_state
supersedes_evidence_id | null
```

Verification states:

- UNVERIFIED
- MACHINE_CHECKED
- HUMAN_VERIFIED
- REJECTED
- SUPERSEDED

Rules:

- raw source form and normalized form must remain distinguishable;
- normalization must not destroy the original reported value/wording;
- confidence is not truth;
- a rejected extraction remains auditable.

## 12. Claim

Claim represents a proposition asserted or materially implied by a source.

Minimum extension:

```text
claim_id = evidence_id
claim_text_normalized
claim_kind
subject_entity_ids[]
predicate
object_entity_ids[]
modality
polarity
scope
qualifiers[]
author_asserted
```

Possible claim kinds:

- HYPOTHESIS
- FINDING
- METHOD_CLAIM
- COMPARATIVE_CLAIM
- CAUSAL_CLAIM
- GENERALIZATION
- INTERPRETATION
- RECOMMENDATION

Modality should preserve distinctions such as:

- demonstrates;
- suggests;
- may;
- is associated with;
- outperforms;
- does not improve.

The engine must not upgrade weak source modality into a stronger claim.

## 13. Method

Minimum extension:

```text
method_id = evidence_id
name
normalized_name
method_family
description
components[]
parameters{}
implementation_artifact_ids[]
```

A Method may be defined by one paper and reused/evaluated by others. Entity
resolution should preserve both the normalized method concept and source-specific
descriptions.

## 14. Experiment

Experiment binds evidence to conditions.

Minimum extension:

```text
experiment_id = evidence_id
research_question_ids[]
hypothesis_ids[]
method_ids[]
baseline_ids[]
dataset_or_population_ids[]
condition_ids[]
sample_size
train_validation_test_design
randomization
replicates
hardware_or_environment
statistical_procedure
```

Unknown fields remain unknown.

Do not infer experimental controls merely because they are conventional.

## 15. DatasetOrPopulation

Minimum extension:

```text
dataset_population_id = evidence_id
name
version
domain
population_description
collection_method
sample_count
unit_of_analysis
time_period
geography_or_environment
inclusion_criteria
exclusion_criteria
known_biases[]
```

For technical datasets, domain-specific extensions may include:

- waveform/protocol;
- sensor/device;
- simulation versus physical capture;
- synthetic versus real;
- train/test provenance.

## 16. Metric

Minimum extension:

```text
metric_id = evidence_id
name
normalized_name
definition
units
direction
aggregation
threshold_or_operating_point
```

The same label can mean different calculations across papers. Metric entity
resolution must therefore preserve source definitions.

## 17. Result

Result is the primary quantitative/qualitative outcome record.

Minimum extension:

```text
result_id = evidence_id
experiment_id
metric_id
method_id | null
comparator_method_id | null
dataset_or_population_id | null
condition_ids[]
raw_value
normalized_value | null
units | null
uncertainty
confidence_interval
standard_deviation
standard_error
p_value
effect_size
sample_count
direction_of_comparison | null
is_primary_result
```

Rules:

- preserve raw_value exactly as represented by the source when possible;
- normalized numerical values must not replace raw values;
- units and operating points are part of the result;
- do not compare results across papers until metric/context compatibility is
  explicitly assessed;
- values extracted from figures/tables should identify that source object.

## 18. Limitation

Minimum extension:

```text
limitation_id = evidence_id
category
description
scope
author_asserted
affected_claim_ids[]
affected_result_ids[]
```

Possible categories:

- DATA
- SAMPLE_SIZE
- GENERALIZATION
- SIMULATION_ONLY
- EXTERNAL_VALIDATION
- BASELINE_COVERAGE
- METRIC
- COMPUTE
- REPRODUCIBILITY
- CONFOUNDING
- MEASUREMENT
- ASSUMPTION
- ACCESS

A model-inferred limitation must set author_asserted=false and must be represented
as inference-backed rather than quoted source fact.

## 19. Inference

Inference is a durable model/human conclusion derived from evidence.

It is explicitly not a source EvidenceObject.

Minimum fields:

```text
inference_id
inference_type
statement
input_evidence_ids[]
input_inference_ids[]
generator_type
generator_identity
generator_version
generated_at
rationale
confidence | null
verification_state
human_decision_id | null
supersedes_inference_id | null
```

Possible types:

- SYNTHESIS
- TAXONOMY
- CONTRADICTION_CANDIDATE
- GAP_CANDIDATE
- NOVELTY_ASSESSMENT
- FEASIBILITY_ASSESSMENT
- PROPOSAL_ARGUMENT

An inference must never be returned as though it were directly stated by a paper.

## 20. EvidenceRelation

EvidenceRelation connects evidence, entities, and inferences.

Minimum fields:

```text
relation_id
source_id
target_id
relation_type
basis_evidence_ids[]
context_compatibility
rationale
confidence | null
verification_state
created_by
created_at
```

Core relation types:

- SUPPORTS
- CONTRADICTS
- QUALIFIES
- REPLICATES
- FAILS_TO_REPLICATE
- EXTENDS
- USES
- EVALUATES
- COMPARES_AGAINST
- MEASURES
- REPORTS
- DERIVED_FROM
- CITES
- SAME_CONCEPT_AS
- VERSION_OF
- MOTIVATES
- CHALLENGES

Contradiction is context-sensitive.

Two results should not be labeled contradictory merely because their numeric
values differ. The relation should assess compatibility across method, metric,
dataset/population, operating point, and experimental conditions.

## 21. VerificationEvent

Verification should be append-only/auditable.

Minimum fields:

```text
verification_event_id
target_id
target_type
verification_type
verifier_type
verifier_identity
verifier_version
result
evidence_or_notes
timestamp
```

Verification types may include:

- LOCATOR_CHECK
- NUMERIC_CHECK
- ENTITY_RESOLUTION_CHECK
- CLAIM_FIDELITY_CHECK
- RELATION_CHECK
- HUMAN_REVIEW
- RETRACTION_CHECK

A verification event changes the current interpreted state but does not erase
prior extraction history.

## 22. SynthesisArtifact

A synthesis is a reproducible generated view over an evidence set.

Minimum fields:

```text
synthesis_id
research_scope_id
question
knowledge_checkpoint
input_evidence_ids[]
input_inference_ids[]
retrieval_run_id
generator_identity
generator_version
generated_at
content
citation_map
known_gaps[]
```

If the underlying evidence changes, the system should be able to mark an old
synthesis stale without deleting it.

## 23. Research-gap representation

A GapCandidate is an Inference with additional structure:

```text
gap_candidate_id
statement
gap_type
motivating_evidence_ids[]
contradicting_evidence_ids[]
repeated_limitation_ids[]
affected_methods[]
affected_datasets_or_populations[]
novelty_status
novelty_search_run_ids[]
feasibility_state
human_review_state
```

GapCandidate states:

- PROPOSED
- UNDER_CHALLENGE
- SUPPORTED_AS_OPEN
- NARROWED
- REJECTED_PRIOR_WORK_FOUND
- NEEDS_HUMAN_REVIEW

The default state is PROPOSED.

No gap begins as "validated novel."

## 24. Novelty challenge contract

For each candidate research contribution:

1. decompose novelty into independently searchable propositions;
2. generate terminology/synonym expansions;
3. run targeted current literature discovery;
4. inspect citation/reference neighborhoods of nearest prior work;
5. search recent work separately;
6. preserve every novelty-search DiscoveryRun;
7. link discovered counterevidence;
8. revise, narrow, reject, or escalate the gap.

A novelty assessment must cite the search checkpoint and evidence corpus on which
it was based.

Novelty can become stale as new literature appears.

## 25. Numerical integrity rules

For quantitative evidence:

- store the raw reported representation;
- store normalized value separately;
- retain units;
- retain metric definition;
- retain operating point/threshold;
- retain uncertainty where reported;
- retain sample size where reported;
- retain source table/figure locator;
- never fabricate missing uncertainty;
- never silently convert percentages/proportions without recording the
  transformation.

Derived calculations are Inference or derived Result records and must point to
their input Result IDs.

## 26. Citation fidelity rules

A generated sentence may cite a paper only when the cited paper's evidence
supports the relevant proposition.

The engine should be able to produce a citation map:

```text
generated span
  -> inference/claim
  -> supporting evidence IDs
  -> paper/version/artifact
  -> source locators
```

Bibliographic relevance alone is not sufficient support.

## 27. Missing-evidence semantics

The engine must distinguish:

- NOT_REPORTED
- NOT_EXTRACTED
- EXTRACTION_FAILED
- FULLTEXT_UNAVAILABLE
- PARSER_UNCERTAIN
- AMBIGUOUS
- NOT_APPLICABLE

"Unknown" is preferable to invented completeness.

## 28. Corrections, retractions, and supersession

When a work is corrected or retracted:

- preserve the original evidence;
- update Work/WorkVersion status;
- create verification/status events;
- identify dependent syntheses/inferences;
- mark affected downstream artifacts for re-evaluation.

Do not erase the historical fact that earlier syntheses used the evidence.

## 29. Minimal query guarantee

Before the evidence contract is considered implemented, the system must be able
to answer a query of the following form:

> Which papers support claim X, what experiments/results support it, under what
> conditions, what limitations qualify it, which papers contradict it, and where
> exactly in each source did the relevant evidence come from?

The answer must be constructible from durable records without rereading every
paper from scratch.

## 30. Pilot annotation target

For the first vertical slice, manually verify a benchmark subset of papers and
annotate at least:

- one research question;
- one method;
- one experiment;
- one dataset/population;
- one metric;
- one quantitative or qualitative result;
- one claim linked to evidence;
- one limitation where present;
- source locators for each extracted evidence object.

This benchmark becomes the ground truth for evaluating automated extraction.

## 31. Contract completion criteria

The v1 evidence contract is ready for implementation design when:

- every scientific synthesis can trace to evidence records;
- every evidence record can trace to a source artifact and qualified locator;
- source claims and generated inference are structurally distinct;
- result comparison preserves metric/context compatibility;
- contradictions can coexist;
- missing data has explicit semantics;
- correction/retraction propagation is representable;
- novelty challenge can be represented as reproducible search evidence;
- no chosen database/storage technology is required to express the model.
