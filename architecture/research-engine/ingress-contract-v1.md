# Research Engine Ingress Contract v1

Status: DRAFT CONTRACT
Parent architecture: ../automated-research-engine-v1.md
Evidence contract: evidence-contract-v1.md
Created: 2026-09-30

## 1. Purpose

The ingress layer turns an external scholarly search result into a reproducible,
auditable corpus without treating provider records, URLs, or PDFs as interchangeable.

The contract separates four concerns:

1. discovery;
2. canonical scholarly identity;
3. lawful source resolution/acquisition;
4. corpus screening state.

The durable unit is not "a list of PDFs." It is a manifest explaining exactly
how each candidate entered the corpus, how duplicate/version relationships were
resolved, what source artifacts were available, and what acquisition attempts
actually succeeded.

## 2. Required state transitions

A candidate work may move through:

```text
DISCOVERED
  -> IDENTITY_PENDING
  -> IDENTITY_RESOLVED
  -> SCREENED
  -> SOURCE_RESOLUTION_PENDING
      -> SOURCE_RESOLVED
      -> METADATA_ONLY
      -> ACCESS_REQUIRED
  -> ACQUISITION_PENDING
      -> ACQUIRED
      -> ACQUISITION_FAILED
  -> READY_FOR_PARSE
```

Discovery, source resolution, and acquisition are separate states.

A provider returning a PDF URL does not prove that the current executor acquired
the bytes.

## 3. DiscoveryRun

A DiscoveryRun records one exact provider query.

Required properties:

- stable engine discovery-run ID;
- provider and adapter identity/version;
- exact query;
- structured filters/sort/pagination;
- execution timestamp;
- provider result/run identity where available;
- ordered returned candidate records;
- parent run/expansion reason when the run derives from another paper or search.

A corpus may contain many DiscoveryRuns.

The raw returned candidate order must be preserved even after deduplication so
search behavior can later be evaluated.

## 4. WorkCandidate

A WorkCandidate is the provider-specific record observed during discovery.

It records:

- provider work identifier;
- title exactly as returned;
- author/citation text or structured authors;
- DOI and other external IDs when available;
- candidate full-text/OA URL when returned;
- source DiscoveryRun;
- result rank;
- raw provider metadata snapshot or durable hash/reference when available.

WorkCandidate is not yet the canonical Work.

## 5. Canonical Work and WorkVersion resolution

Identity resolution may use:

- DOI equality;
- arXiv/PMID/PMCID identity;
- publisher identifiers;
- exact normalized title plus author/year evidence;
- version relationships from provider metadata;
- content hashes after acquisition.

Resolution outcomes:

- NEW_WORK
- SAME_WORK_SAME_VERSION
- SAME_WORK_DIFFERENT_VERSION
- POSSIBLE_DUPLICATE
- DISTINCT_WORK
- NEEDS_REVIEW

Do not automatically merge on title similarity alone.

The same intellectual work can legitimately have:

- multiple OpenAlex records;
- preprint and version-of-record records;
- repository and publisher manifestations;
- corrected/superseded versions.

## 6. Source resolution

Source resolution asks:

> What lawful source representations are known for this WorkVersion?

Each SourceLocation records:

- provider;
- URI/identifier;
- source class;
- OA/access class;
- license if known;
- content format if known;
- whether the location is machine-retrievable in the current execution context;
- resolution timestamp.

Source classes may include:

- OPENALEX_CACHED_PDF
- OPENALEX_CACHED_TEI
- ARXIV
- PUBMED_CENTRAL
- INSTITUTIONAL_REPOSITORY
- AUTHOR_REPOSITORY
- PUBLISHER_OA
- PUBLISHER_LICENSED
- USER_SUPPLIED
- OTHER_REPOSITORY

Resolution is not acquisition.

## 7. AcquisitionAttempt

Each attempt records:

- target SourceLocation;
- executor/tool identity;
- start/end timestamp;
- result;
- HTTP/provider status when available;
- failure category;
- acquired byte length;
- cryptographic content hash when bytes were acquired;
- retained artifact identifier/path when permitted.

Results:

- ACQUIRED
- NOT_ATTEMPTED
- ACCESS_REQUIRED
- NETWORK_UNAVAILABLE
- PROVIDER_REJECTED
- NOT_FOUND
- LICENSE_RESTRICTION
- PARSER_UNSUPPORTED
- OTHER_FAILURE

An OA source can resolve successfully while acquisition fails because a particular
executor lacks network access. That is not evidence that the paper is unavailable.

## 8. CorpusManifest

A CorpusManifest binds:

- research scope/question;
- DiscoveryRuns;
- all observed WorkCandidates;
- canonical Work/WorkVersion resolutions;
- screening decisions;
- source locations;
- acquisition attempts;
- selected deep-reading set;
- manifest checkpoint/version.

The manifest is append/revision friendly: later discovery runs may add new works
without rewriting historical search evidence.

## 9. Screening

Screening must preserve the decision and its basis.

Suggested states:

- INCLUDE_DEEP_READ
- INCLUDE_METADATA_ONLY
- DEFER
- EXCLUDE_IRRELEVANT
- EXCLUDE_DUPLICATE
- EXCLUDE_WRONG_VERSION
- EXCLUDE_SCOPE
- EXCLUDE_ACCESS_LIMITATION

A model screening decision remains distinguishable from a human decision.

## 10. Provider independence

The initial pilot uses an OpenAlex-backed scholarly connector because it is
available in the current executor.

That connector is an adapter, not the architecture.

The implementation must permit equivalent DiscoveryRun and SourceLocation records
from OpenAlex, Crossref, Semantic Scholar, Unpaywall, arXiv, PubMed Central,
publisher APIs, institutional repositories, and user-provided documents.

## 11. Pilot findings — 2026-09-30

The first focused RF/open-set pilot used three searches:

1. `"Open Set RF Fingerprinting" generative outlier`
2. `"Open Set Wireless Transmitter Authorization"`
3. `"Automatic Modulation Open Set Recognition"`

The bounded fixture preserves 22 raw result records across those three searches.

Observed behaviors that the implementation must handle:

- provider search precision varies sharply with terminology;
- broad "RF" queries return substantial biomedical/remote-sensing noise;
- the same OpenAlex work can appear in multiple DiscoveryRuns;
- two OpenAlex IDs can represent what appears to be the same intellectual work
  and same arXiv manifestation;
- preprint and published/repository manifestations can coexist;
- resolved OA URL does not imply bytes have been acquired by the current executor.

These are now regression requirements, not incidental observations.

## 12. Implementation boundary

The research-engine executable implementation belongs in a dedicated repository,
currently designated:

`adamtrott78/research-engine`

workspace-control retains:

- cross-project execution policy;
- durable task state;
- architecture contracts during bootstrap;
- reusable schemas/fixtures required to establish the implementation boundary.

Do not grow a production scholarly-ingress application inside workspace-control.

## 13. Ingress v1 completion criteria

Ingress v1 is ready for extraction work when it can:

- reproduce a search manifest from explicit DiscoveryRun records;
- preserve raw provider candidates and ranking;
- deduplicate repeated provider records without erasing provenance;
- represent preprint/published/version relationships;
- resolve lawful source locations independently of acquisition;
- acquire at least one source artifact and store its content hash;
- preserve failed acquisition attempts without misclassifying source availability;
- select a deep-reading subset through explicit CorpusDecision records;
- emit objects conforming to the evidence contract's Work, WorkVersion, and
  SourceArtifact requirements.
