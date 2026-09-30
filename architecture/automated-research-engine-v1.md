# Automated Research Engine v1 Architecture

Status: DRAFT
Owner: workspace-control / research-engine
Initial branch: automated-research-engine-v1
Created: 2026-09-30

## 1. Mission

Build a provenance-preserving automated research system that can discover scholarly
literature, lawfully acquire available full text, extract structured scientific
evidence, accumulate a durable knowledge base, identify and challenge candidate
research gaps, convert selected gaps into fundable research proposals, and hand an
approved research program directly into executable workspace-control workflows.

The long-term loop is:

```text
literature
  -> evidence
  -> structured knowledge
  -> synthesis
  -> candidate gaps
  -> novelty challenge
  -> research directions
  -> proposals
  -> approved research projects
  -> experiments/results/papers
  -> literature
```

The system is not an autonomous replacement for scientific judgment. It is an
execution and evidence system that makes scientific judgment dramatically more
informed, reproducible, scalable, and recoverable.

## 2. Relationship to workspace-control

workspace-control is the execution/control plane.

The research engine is a domain workflow system that runs on top of it.

workspace-control owns generic concerns such as:

- durable task state;
- executor selection and handoff;
- remote/local/composed execution topology;
- mutation scope;
- worktree safety;
- suspension/resume;
- checkpoint identity;
- artifact lifecycle;
- validation gates;
- human decision gates.

The research engine owns research-specific concerns such as:

- literature discovery;
- bibliographic identity;
- lawful content acquisition;
- paper parsing;
- evidence extraction;
- claim/method/result representation;
- scholarly provenance;
- evidence synthesis;
- contradiction detection;
- research-gap generation;
- novelty challenge;
- research-program design;
- funding-opportunity matching;
- proposal generation;
- transition into a project-specific research workflow.

Project repositories such as PADataset remain authoritative for project/domain
truth and execution.

## 3. Core architectural principle

> Store evidence and provenance, not merely AI prose.

Generated prose is cheap and reproducible.

The expensive durable asset is a structured representation that can answer:

- what did a paper actually claim?
- where in the source did the claim occur?
- what method produced the result?
- which dataset, population, waveform, benchmark, or environment was used?
- what metric was measured?
- what result value was reported?
- what limitations or assumptions constrain interpretation?
- which other papers support, refine, or contradict the claim?
- which statements are source-derived facts versus model-generated inference?

Every durable scientific statement must therefore retain a provenance path back to
a source artifact and source location whenever the available source representation
permits it.

## 4. Non-negotiable invariants

### 4.1 Provenance before synthesis

A synthesized statement may cite or aggregate evidence objects, but it must not
replace them.

### 4.2 Source-derived versus inferred knowledge is explicit

The knowledge system must distinguish:

- source metadata;
- extracted source evidence;
- normalized scientific entities;
- cross-paper synthesis;
- model inference;
- human judgment.

These layers must not be silently collapsed.

### 4.3 Novelty is challenged, not asserted

A model may generate a candidate gap.

A candidate gap is not a validated research gap until the system performs a
targeted novelty search designed to disprove it.

### 4.4 Contradiction is first-class

Conflicting findings must coexist with their experimental context. The system must
not silently average, reconcile, or choose between contradictory results.

### 4.5 Acquisition must be lawful

The engine may use:

- open-access sources;
- author/institution repositories;
- preprint servers;
- machine-readable content explicitly exposed for programmatic use;
- licensed institutional access when the applicable license permits the intended
  access and text/data-mining use;
- user-provided documents.

The engine must not bypass paywalls, authentication controls, or access
restrictions.

### 4.6 Provider independence

No single search engine, publisher, index, vector database, LLM, or PDF parser is
the research engine.

External systems are adapters.

### 4.7 Scale through staged triage

"Read thousands of papers" does not mean apply the most expensive deep-reading
pipeline to every discovered document.

The normal funnel is:

```text
large metadata corpus
    -> deduplication
    -> abstract/title screening
    -> topical clustering
    -> relevance ranking
    -> selected full-text acquisition
    -> deep structured reading
    -> evidence graph
```

### 4.8 Human gates remain explicit

At minimum, human approval is required before:

- adopting a high-level research direction as an active program;
- treating a consequential model inference as accepted scientific judgment;
- submitting a funding proposal;
- beginning expensive/high-risk experimental execution when the workflow calls
  for approval.

## 5. System layers

### Layer 0 — Control plane

workspace-control provides durable execution, task state, checkpoints, executor
handoff, artifacts, validation, and suspension/resume.

### Layer 1 — Literature discovery

Purpose:

- discover potentially relevant scholarly works;
- expand from queries, seed papers, citations, references, authors, venues, and
  related-work recommendations;
- preserve the exact discovery path so corpus construction is reproducible.

Inputs may include:

- research questions;
- seed DOI/OpenAlex/Semantic Scholar/arXiv/PMID identifiers;
- known authors;
- venues;
- date ranges;
- inclusion/exclusion rules;
- prior knowledge-graph nodes.

Outputs:

- canonical work candidates;
- discovery provenance;
- relevance-screening state.

### Layer 2 — Bibliographic canonicalization

Resolve multiple records for one intellectual work into a canonical paper identity
while preserving versions.

Potential identifiers:

- DOI;
- OpenAlex work ID;
- Semantic Scholar paper ID/corpus ID;
- PMID/PMCID;
- arXiv ID;
- publisher URL;
- repository identifier.

Do not collapse a preprint, accepted manuscript, and version of record without
preserving their version relationship.

### Layer 3 — Acquisition resolver

For each work, resolve the best lawful machine-readable source.

Candidate adapter order may include:

1. OpenAlex work locations and cached content;
2. subject/institutional repositories;
3. Crossref metadata-provided TDM/full-text links;
4. Unpaywall DOI-level OA resolution;
5. arXiv/PMC/domain repositories;
6. publisher or institutional access when explicitly permitted;
7. user-supplied PDF/document;
8. metadata/abstract-only fallback.

The acquisition resolver records:

- source provider;
- source URL/identifier;
- access type;
- license when known;
- version;
- retrieval timestamp;
- content hash;
- format;
- parser eligibility;
- acquisition failure reason when unavailable.

A work may be useful even when full text is unavailable, but its evidence state
must reflect that limitation.

### Layer 4 — Document normalization and parsing

Preferred source forms:

1. trusted structured full text such as TEI/XML/JATS;
2. born-digital PDF with reliable text/layout extraction;
3. repository HTML/full text;
4. OCR only when required.

The normalized document representation should retain:

- document hierarchy;
- section headings;
- paragraph/span boundaries;
- page anchors when available;
- tables;
- figure captions;
- equations when useful;
- references;
- source offsets/coordinates sufficient for traceability.

### Layer 5 — Structured scientific extraction

Deep reading should extract typed objects rather than only narrative summaries.

Candidate object classes:

- ResearchQuestion
- Hypothesis
- Claim
- Method
- Algorithm
- Model
- Dataset
- Population
- Environment
- ExperimentalCondition
- Baseline
- Metric
- Result
- Limitation
- Assumption
- ThreatToValidity
- FutureWork
- Artifact
- FundingSource

Every extracted object includes provenance.

A Result, for example, should be able to encode:

```text
paper
experiment
condition
method
dataset/population
metric
value/range
comparison
source location
extraction confidence
verification state
```

### Layer 6 — Evidence graph / durable knowledge base

The durable knowledge layer is a graph of typed entities and relationships backed
by immutable source identities.

Example edges:

```text
Paper --proposes--> Method
Paper --evaluates--> Method
Method --evaluated_on--> Dataset
Experiment --uses--> Method
Experiment --compares_against--> Baseline
Experiment --reports--> Result
Result --measures--> Metric
Claim --supported_by--> Result
Claim --qualified_by--> Limitation
Paper --cites--> Paper
Claim --supports--> Claim
Claim --contradicts--> Claim
Method --extends--> Method
GapCandidate --motivated_by--> EvidenceSet
GapCandidate --challenged_by--> SearchRun
ResearchProgram --addresses--> GapCandidate
```

The graph must preserve many-to-many relationships and disagreement.

### Layer 7 — Retrieval and synthesis

The synthesis layer answers research questions by retrieving evidence objects,
not by relying on one monolithic summary.

Outputs may include:

- state-of-the-art maps;
- method taxonomies;
- chronological development;
- benchmark comparisons;
- recurring limitations;
- methodological trends;
- contradictory findings;
- underexplored combinations;
- evidence-strength assessments.

Each generated synthesis remains reproducible from an evidence set.

### Layer 8 — Research-gap engine

Gap generation operates over evidence patterns.

Candidate gap signals include:

- repeated explicit limitations;
- repeated future-work proposals that remain unaddressed;
- contradictory results under poorly controlled conditions;
- missing external/real-world validation;
- simulation-only validation;
- missing cross-domain evaluation;
- missing baselines;
- sparse method × dataset combinations;
- obsolete benchmarks;
- untested assumptions;
- missing uncertainty/error analysis;
- inaccessible/reproducibility-limited methods;
- new technical capabilities that make previously infeasible questions testable.

A model-generated candidate is stored as GapCandidate, not Fact.

### Layer 9 — Novelty challenge

For each promising GapCandidate, generate adversarial searches intended to find
prior work that invalidates the novelty claim.

The process should:

1. decompose the proposed contribution into searchable claims;
2. search synonyms and adjacent terminology;
3. inspect citation neighborhoods;
4. search recent work separately;
5. search likely competing venues/authors;
6. record discovered counterevidence;
7. revise, narrow, or reject the gap.

Possible states:

- PROPOSED;
- UNDER_CHALLENGE;
- SUPPORTED_AS_OPEN;
- NARROWED;
- REJECTED_PRIOR_WORK_FOUND;
- NEEDS_HUMAN_REVIEW.

### Layer 10 — Research-program generator

A supported gap can be expanded into a candidate research program containing:

- problem statement;
- research question;
- hypotheses;
- proposed contribution;
- experiment design;
- required data;
- required infrastructure;
- baselines;
- evaluation metrics;
- falsification criteria;
- risk register;
- dependencies;
- expected artifacts;
- preliminary-work requirements;
- estimated cost/runtime;
- ethical/regulatory considerations when relevant.

The program should explicitly distinguish what is already available from what must
be built.

### Layer 11 — Funding-opportunity and proposal layer

The system may continuously or on-demand match candidate programs against current
funding opportunities.

For NSF-oriented work, opportunity sources may include official NSF solicitation
pages/RSS and federal Grants.gov opportunity APIs.

The proposal compiler should map validated research evidence into a solicitation-
specific proposal package, not generate one generic NSF document.

Candidate outputs:

- solicitation requirements matrix;
- project summary;
- intellectual merit argument;
- broader impacts argument;
- project description;
- related-work/state-of-the-art evidence;
- objectives and hypotheses;
- work packages;
- evaluation plan;
- timeline;
- risk/mitigation;
- facilities/resources mapping;
- data-management/security inputs;
- citation package;
- unresolved author/human inputs.

Proposal submission remains a human gate.

### Layer 12 — Execution bridge

When a research program is approved:

1. create/select the owning project repository;
2. create a workspace-control task capsule;
3. bind exact reusable workflow versions;
4. provision an isolated branch/worktree if required;
5. materialize the experiment plan;
6. execute data collection/training/evaluation;
7. persist results and provenance;
8. generate analyses/figures;
9. write and validate papers;
10. feed resulting publications/evidence back into the research knowledge base.

This is the bridge from "knowledge about a gap" to "research actively testing the
gap."

## 6. Paper lifecycle

A paper/work may move through:

```text
DISCOVERED
  -> IDENTITY_RESOLVED
  -> SCREENED
  -> ACQUISITION_PENDING
      -> FULLTEXT_AVAILABLE
      -> ABSTRACT_ONLY
      -> ACCESS_REQUIRED
      -> ACQUISITION_FAILED
  -> PARSED
  -> EXTRACTED
  -> VERIFIED
  -> INDEXED
```

Separate flags should capture:

- retraction/correction status;
- version relation;
- source/license;
- extraction confidence;
- human verification;
- relevance/inclusion status.

## 7. Provenance model

Minimum provenance for an extracted evidence object:

```text
source_work_id
source_version_id
source_artifact_hash
source_section
source_page_or_anchor
source_span_or_locator
extractor_identity
extraction_timestamp
extraction_model_or_tool
extraction_confidence
verification_state
```

Where a precise page/span cannot be recovered, the provenance object must say so
rather than inventing precision.

## 8. Trust boundaries

### Immutable/source layer

Contains acquired artifacts and bibliographic/source metadata.

### Extracted evidence layer

Contains typed claims/results/methods linked directly to sources.

### Normalized knowledge layer

Resolves equivalent concepts and entities without deleting source-specific
representations.

### Synthesis layer

Contains generated cross-paper interpretation.

### Decision layer

Contains human-approved directions, proposal choices, and execution decisions.

A downstream layer may reference an upstream layer. It must not silently overwrite
it.

## 9. Search and acquisition landscape — initial adapters

This list is deliberately adapter-oriented rather than provider-dependent.

### OpenAlex

Useful for:

- large-scale scholarly work discovery;
- citation/reference metadata;
- work locations;
- OA resolution;
- cached open-access PDF/TEI content where available.

Current public documentation (checked 2026-09-30) reports cached full text for
more than 50 million open-access works, with machine-readable TEI XML for roughly
43 million.

References:

- https://help.openalex.org/data/locations/
- https://help.openalex.org/access/fulltext/

### Crossref

Useful for:

- DOI metadata;
- bibliographic metadata;
- funder/license information;
- post-publication metadata;
- some full-text/TDM links deposited by publishers.

Crossref itself is primarily a metadata provider; full-text URLs may be exposed in
metadata where deposited.

References:

- https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- https://www.crossref.org/documentation/retrieve-metadata/rest-api/text-and-data-mining/

### Unpaywall

Useful for:

- DOI-level OA status and legal OA locations.

As of 2026-09-30, DOI lookup remains available while Unpaywall's general search
endpoint has been retired in favor of OpenAlex search.

Reference:

- https://data.unpaywall.org/products/api

### Semantic Scholar

Useful for:

- academic graph metadata;
- citation/reference traversal;
- recommendations;
- bulk datasets.

References:

- https://api.semanticscholar.org/api-docs
- https://api.semanticscholar.org/api-docs/snippets

### Domain repositories

Examples include arXiv and PubMed Central.

Prefer repository-native structured sources where available.

### Grants.gov / NSF

Grants.gov currently exposes programmatic opportunity search and opportunity-detail
retrieval. NSF also publishes funding-opportunity and due-date feeds.

References:

- https://www.grants.gov/api/api-guide
- https://www.nsf.gov/rss

## 10. Corpus construction

A research corpus is a reproducible artifact.

Store:

- initial question;
- seed works;
- queries;
- provider;
- query parameters;
- filters;
- search timestamp;
- result identifiers;
- inclusion/exclusion decisions;
- citation expansion operations;
- deduplication decisions;
- final screening state.

This permits later questions such as:

- What did we search?
- What did we miss because of the query?
- When was the search last refreshed?
- Which new papers appeared after the original synthesis?

## 11. Incremental knowledge updates

The system should never require rereading the entire world because one new paper
arrived.

New work should trigger:

1. identity/deduplication;
2. relevance screening;
3. acquisition;
4. extraction;
5. entity resolution;
6. graph insertion;
7. affected-synthesis invalidation;
8. contradiction/gap re-evaluation only where impacted.

Syntheses should therefore declare the evidence set and knowledge checkpoint they
were built from.

## 12. Research-gap ranking

Gap candidates may be ranked using dimensions such as:

- scientific importance;
- evidence that the gap is genuinely open;
- expected novelty;
- tractability;
- availability of data;
- availability of infrastructure;
- fit with existing project assets;
- time/cost;
- methodological risk;
- funding relevance;
- potential impact.

The ranking must expose its criteria rather than collapsing judgment into one
opaque model score.

For project-specific planning, a particularly useful objective is:

```text
literature gap
x scientific importance
x novelty confidence
x feasibility
x existing assets
x funding fit
```

This can identify not merely unanswered questions, but unanswered questions the
researcher is unusually well-positioned to attack.

## 13. First vertical slice

Do not begin by attempting to ingest millions of papers.

The first useful end-to-end experiment should use a narrow domain close to current
expertise, for example open-set/open-world RF sensing and RF signal
classification.

Suggested pilot:

1. define 5-10 benchmark research questions;
2. provide 10-20 known seed papers;
3. discover several hundred candidate works;
4. deduplicate and screen the metadata corpus;
5. acquire/deep-read approximately 50-100 high-value works;
6. extract typed evidence;
7. build the evidence graph;
8. answer the benchmark questions with traceable provenance;
9. identify contradictions and candidate gaps;
10. perform novelty-challenge searches on the best gaps;
11. compare system outputs with expert/manual understanding.

The goal of v1 is not maximum corpus size.

The goal is to prove that increased corpus size produces better durable knowledge
rather than larger quantities of untraceable generated text.

## 14. Success metrics

### Ingress

- discovery recall on benchmark seed sets;
- identifier-resolution accuracy;
- duplicate/version resolution accuracy;
- lawful full-text acquisition rate;
- acquisition provenance completeness.

### Extraction

- claim extraction precision/recall on manually annotated samples;
- method/dataset/metric/result linking accuracy;
- numerical result fidelity;
- source-locator accuracy;
- unsupported-extraction rate.

### Knowledge

- provenance completeness;
- contradiction retrieval;
- entity-resolution accuracy;
- query answer traceability;
- stale-synthesis detection.

### Gap engine

- fraction of candidate gaps invalidated by novelty challenge;
- expert agreement that surviving gaps are meaningfully open;
- usefulness/tractability of generated research directions;
- false-novelty rate.

### Proposal layer

- solicitation-requirement coverage;
- evidence traceability;
- unsupported-claim rate;
- amount of unresolved human input;
- reviewer/human evaluation.

### Execution bridge

- ability to create an exact project workflow from an approved research program;
- reproducibility of the handoff;
- percentage of proposal research plan represented as executable task state.

## 15. Initial implementation phases

### Phase 0 — Architecture and evidence contract

Define:

- canonical entities;
- provenance requirements;
- corpus/search records;
- evidence versus inference boundaries;
- minimum vertical-slice benchmark.

### Phase 1 — Discovery and acquisition resolver

Implement adapters, canonical identity resolution, access-state tracking, content
hashing, and lawful full-text retrieval.

### Phase 2 — Parsing and structured evidence extraction

Implement normalized document representation plus typed evidence extraction and
verification.

### Phase 3 — Evidence graph and retrieval

Persist typed entities/edges and support provenance-preserving queries.

### Phase 4 — Synthesis and contradiction engine

Generate reproducible cross-paper syntheses and identify conflicts/uncertainty.

### Phase 5 — Gap generation and novelty challenge

Generate evidence-grounded gap candidates and adversarially search for prior work
that invalidates them.

### Phase 6 — Research-program and proposal compiler

Turn surviving gaps into research programs, match opportunities, and produce
solicitation-specific proposal artifacts.

### Phase 7 — Execution bridge

Instantiate approved programs as project repositories/workflows/task capsules and
feed resulting evidence back into the knowledge base.

## 16. Open design questions

These are intentionally unresolved at architecture start:

- primary persistence model: relational, graph, hybrid, or event + derived index;
- canonical schema for scientific evidence objects;
- embedding/vector-index role versus structured graph role;
- parser stack for PDF/TEI/JATS/HTML;
- verification model for extracted numerical results and tables;
- versioning model for knowledge graph snapshots;
- institutional-access/TDM integration boundaries;
- compute/cost controls for large corpora;
- model selection by task class;
- active-learning strategy for human verification;
- citation-context extraction;
- treatment of surveys/meta-analyses versus primary studies;
- retraction/correction propagation;
- proposal solicitation parser;
- project bootstrap contract for execution.

## 17. Immediate next question

The first design decision should be the **evidence contract**, not the database or
UI.

Before choosing storage technology, define exactly what it means for the engine to
say:

> "Paper A provides evidence for claim X under conditions Y."

Once that object is trustworthy, search, graph storage, synthesis, gap inference,
and proposal generation can all be built around it.


## 18. Evidence contract

The detailed v1 evidence/provenance contract is maintained at:

- [research-engine/evidence-contract-v1.md](research-engine/evidence-contract-v1.md)

That contract defines the minimum durable objects and traceability path required
before persistence technology is selected.

The core support path is:

```text
scientific statement
  -> evidence object / relation
  -> result or source claim
  -> experiment/method/context
  -> work version
  -> immutable source artifact
  -> exact/qualified source locator
```

Generated synthesis and inference must point into that graph rather than replacing
it.
