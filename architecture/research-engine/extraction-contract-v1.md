# Research Engine Extraction Contract v1

Status: DRAFT CONTRACT
Parent architecture: ../automated-research-engine-v1.md
Evidence contract: evidence-contract-v1.md
Ingress contract: ingress-contract-v1.md
Created: 2026-09-30

## 1. Purpose

The extraction layer converts an acquired or metadata-only scholarly source into a
normalized document representation and typed scientific evidence without
collapsing source text, normalized interpretation, and model inference.

## 2. Extraction levels

The engine must record the maximum source level actually available:

- METADATA_ONLY
- ABSTRACT_ONLY
- FULLTEXT_STRUCTURED
- FULLTEXT_PDF_TEXT
- FULLTEXT_PDF_LAYOUT
- OCR_DERIVED

An extraction at ABSTRACT_ONLY is valid for claims supported by the abstract. It
must not silently fabricate method details, table values, page numbers, or
limitations that require full text.

## 3. NormalizedDocument

A NormalizedDocument binds:

- SourceArtifact or metadata-source identity;
- parser/extractor identity;
- source level;
- ordered structural blocks;
- stable locator identifiers;
- normalized text;
- parser warnings.

A block may represent:

- title;
- abstract;
- section heading;
- paragraph;
- equation;
- table;
- table cell/range;
- figure;
- figure caption;
- reference.

## 4. SourceLocator

A SourceLocator identifies exactly where source-derived evidence came from.

Locator precision must be explicit:

- EXACT: exact span/bbox/XML node is known;
- STRUCTURAL: exact section/block known, span precision unavailable;
- APPROXIMATE: coarse location only;
- UNAVAILABLE: source supports the evidence but the current representation cannot
  expose a stable locator.

An abstract supplied as one provider field can use a STRUCTURAL locator such as
`abstract`, but it must not claim a PDF page number.

## 5. ExtractionRun

Every extraction run records:

- source identity;
- source level;
- parser/tool/model identity;
- extraction instructions/schema version;
- timestamp;
- output evidence IDs;
- warnings/failures;
- verification state.

Rerunning extraction produces a new run; it does not silently overwrite previous
evidence.

## 6. Typed extraction order

The initial deep-reading order is:

1. ResearchQuestion / problem framing;
2. Claim;
3. Method;
4. Experiment;
5. DatasetOrPopulation;
6. Metric;
7. Result;
8. Limitation / assumption / threat;
9. EvidenceRelation.

The extractor should first capture source objects and only afterward create
cross-object relations.

## 7. Raw versus normalized representation

Each EvidenceObject stores:

- raw source form when available;
- normalized form;
- source locator;
- extraction identity;
- verification state.

Normalization may standardize names, units, or terminology, but may not erase the
reported source form.

## 8. Quantitative evidence

Numeric extraction requires:

- exact raw value;
- normalized numeric value separately;
- units;
- metric definition/reference;
- condition/operating point;
- uncertainty when reported;
- sample size when reported;
- table/figure/text locator.

If any field is absent, record it as absent. Do not infer conventional values.

## 9. Claim modality

The extractor must preserve source modality.

For example:

- "demonstrates" is stronger than "suggests";
- "can" is stronger than "may";
- "significant increase" without a numerical value remains a qualitative result
  unless the full text provides the value.

## 10. Model inference boundary

If the system concludes something not directly asserted by the source, store an
Inference linked to source EvidenceObjects.

Do not put model-generated interpretation into Claim.raw_source_form.

## 11. Verification

Initial machine checks should include:

- locator exists in the normalized source;
- quoted/raw text matches the source block;
- numeric value round-trips to source text/table;
- referenced entity IDs exist;
- Claim/Result relations do not point across incompatible experiments without an
  explicit relation rationale.

Human verification can promote critical benchmark evidence to HUMAN_VERIFIED.

## 12. First-paper benchmark

The first extraction target is:

`Open Set RF Fingerprinting using Generative Outlier Augmentation`
arXiv `2108.13099v1`

Acquired artifact:

- bytes: 816786
- SHA-256: `7fcfc9929fd80a94095657ebf644be3301000d0a4342b74de1adc2af529ff7ab`

Before the exact PDF is available to an extraction executor, only the authoritative
arXiv abstract may be used, and the fixture must remain ABSTRACT_ONLY.

Full-paper benchmark completion requires the exact content-hashed PDF and stable
page/section/block locators.
