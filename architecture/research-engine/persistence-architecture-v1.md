# Research Engine Persistence Architecture v1

Status: DECISION
Parent architecture: ../automated-research-engine-v1.md
Decision date: 2026-09-30

## 1. Decision

Use **PostgreSQL 18** as the v1 authoritative structured knowledge store.

Use **pgvector** as an optional semantic-retrieval extension inside PostgreSQL.

Use a content-addressed artifact store outside relational rows for retained source
bytes (PDF/TEI/XML/HTML/provider responses), with SHA-256 identities and artifact
metadata stored in PostgreSQL.

Do **not** introduce a separate graph database in v1.

Do **not** make a vector index authoritative.

## 2. Why this decision is now justified

The vertical slice has demonstrated the actual requirements:

- immutable Work / WorkVersion / SourceArtifact identity;
- typed EvidenceObject records;
- exact and qualified SourceLocator records;
- append/auditable acquisition, extraction, and verification history;
- directed EvidenceRelation edges;
- recursive evidence -> relation -> source provenance queries;
- structured filters over evidence type, verification state, domain, work, source
  fidelity, and dates;
- flexible type-specific attributes;
- lexical full-text/metadata retrieval;
- semantic retrieval over papers/evidence/syntheses;
- transactional ingestion and deduplication;
- multiple executors writing durable state concurrently;
- corpus sizes expected to start in hundreds/thousands of works rather than
  internet-scale billions.

These requirements fit one relational system cleanly.

## 3. Authority layers

### Authoritative

PostgreSQL stores the authoritative structured records:

- works;
- work_versions;
- external_identifiers;
- source_artifacts;
- source_locations;
- source_locators;
- discovery_runs;
- work_candidates;
- corpus_decisions;
- acquisition_attempts;
- extraction_runs;
- evidence_objects;
- evidence_relations;
- inferences;
- verification_events;
- synthesis_artifacts;
- gap_candidates;
- novelty_challenges;
- research_programs;
- funding_opportunities;
- solicitation_requirements;
- proposal_compilations;
- execution_bridge_plans.

### Authoritative source bytes

Retained source content is stored by content hash in a content-addressed artifact
store.

Conceptual path:

```text
sha256/7f/cf/7fcfc9929fd80a...
```

The database records:

- SHA-256;
- byte length;
- media type;
- access/license state;
- acquisition provenance;
- artifact-store URI/path.

A file location is not its identity. The content hash is.

### Rebuildable projections

The following are derived and may be rebuilt:

- graph traversal convenience views;
- materialized graph summaries;
- text-search vectors;
- embeddings;
- vector indexes;
- similarity neighborhoods;
- cached syntheses;
- ranking features.

Loss of a projection must not destroy scientific evidence.

## 4. Relational core

Prefer explicit columns for stable contract fields and JSONB for type-specific
extension attributes.

For example:

```text
evidence_objects
  id
  evidence_type
  work_id
  work_version_id
  source_artifact_id
  source_locator_id
  raw_source_form
  normalized_form
  extraction_run_id
  extractor_identity
  verification_state
  created_at
  supersedes_id
  attributes JSONB
```

Do not put the entire EvidenceObject into one opaque JSON document.

Stable identity, provenance, verification, and relationship fields belong in
typed relational columns.

JSONB is for extensibility such as:

- experiment-specific parameters;
- metric-specific details;
- domain-specific RF metadata;
- result uncertainty/value variants;
- method-specific configuration.

## 5. Directed evidence graph

Represent the graph as ordinary relational adjacency tables.

Conceptual core:

```text
evidence_relations
  id
  source_id
  target_id
  relation_type
  context_compatibility
  verification_state
  rationale
  attributes JSONB
```

Use indexes on:

- source_id;
- target_id;
- relation_type;
- (source_id, relation_type);
- (target_id, relation_type).

Use recursive CTEs for multi-hop provenance/lineage traversal.

The five-work vertical slice requires paths on the order of a few hops:

```text
Synthesis statement
  -> Result
  -> Experiment
  -> Method
  -> SourceLocator
  -> SourceArtifact
  -> WorkVersion
  -> Work
```

A dedicated graph database is not justified until measured workloads demonstrate
that PostgreSQL adjacency traversal is inadequate.

## 6. Lexical retrieval

Use PostgreSQL full-text search for:

- titles;
- abstracts;
- normalized evidence text;
- method names;
- limitations;
- synthesis text.

Lexical search is important even after semantic retrieval exists because:

- exact terminology matters for novelty challenge;
- acronym/method names matter;
- citation/source lookup benefits from deterministic token matching;
- semantic embeddings must not be the only retrieval path.

## 7. Semantic retrieval

Use pgvector inside PostgreSQL for embeddings over selected records such as:

- work title + abstract;
- evidence normalized_form;
- synthesis statements;
- gap candidates;
- method descriptions.

Start with **exact nearest-neighbor search**.

Do not create approximate indexes merely because HNSW/IVFFlat are available.

Add HNSW only after the corpus/query benchmark shows exact search is materially
too slow and measure recall against exact search.

Embedding records must include:

- embedding model/provider;
- model version;
- dimensions;
- source record ID;
- source record content hash/version;
- created_at.

Changing embedding model creates a new embedding projection rather than mutating
scientific evidence.

## 8. Why not Neo4j / separate graph store in v1

A second graph database would introduce:

- duplicate identity/state;
- graph synchronization;
- additional backup/restore semantics;
- another migration path;
- potential disagreement between relational evidence and graph state.

The demonstrated graph is naturally represented as typed nodes plus directed
relation rows.

A separate graph engine may be introduced later only as a rebuildable projection
if measured graph workloads justify it.

## 9. Why not vector-database-first

The engine's primary queries are not only similarity queries.

Examples already demonstrated:

- exact artifact -> evidence -> result provenance;
- find all limitations qualifying a method;
- distinguish OCR-derived from exact-PDF evidence;
- traverse Result --SUPPORTS--> Claim;
- filter by verification state;
- identify all claims affected by a retracted WorkVersion;
- reproduce a corpus DiscoveryRun;
- preserve supersession/history.

A vector database is useful for retrieval, not for representing those contracts.

## 10. Content-addressed artifact store

v1 may begin with a filesystem-backed store.

Required semantics:

- atomic write;
- verify SHA-256 before commit;
- immutable path after commit;
- deduplicate identical bytes;
- side metadata in PostgreSQL;
- no inferred deletion from loss of a URL;
- access/license state tracked independently of byte identity.

The storage adapter should later support S3-compatible object storage without
changing SourceArtifact identity.

## 11. Append/audit behavior

Prefer append-only or superseding records for:

- acquisition attempts;
- extraction runs;
- verification events;
- screening decisions;
- novelty challenge runs;
- human decisions.

Current state may be exposed through views, but historical events remain
queryable.

## 12. Concurrency

PostgreSQL is the right v1 boundary for multiple agents/executors because
canonicalization and ingestion need transactional guarantees.

Examples:

- two discovery adapters resolving the same DOI;
- two workers attempting to create one WorkVersion;
- concurrent evidence extraction;
- verification arriving while synthesis reads a checkpoint.

Use unique constraints plus transactions rather than coordinating identity only
in application memory.

## 13. Initial index strategy

Relational:

- unique external identifier indexes;
- B-tree indexes for foreign keys/state/date/type;
- GIN indexes on selected JSONB fields only where measured;
- GIN full-text indexes on searchable text projections.

Vector:

- exact search initially;
- HNSW later if benchmarked;
- IVFFlat only if its build/memory tradeoff is preferable for a measured workload.

Do not optimize hypothetical scale.

## 14. Knowledge checkpoints

A synthesis must be reproducible against a logical knowledge checkpoint.

The implementation should support a checkpoint identity derived from:

- authoritative record revisions/events;
- corpus membership;
- extraction/verification states.

Do not rely on "whatever is in the live DB now" as the only reproducibility
mechanism.

## 15. v1 service boundary

The future `adamtrott78/research-engine` implementation should expose application
services roughly along these boundaries:

- discovery;
- identity resolution;
- acquisition;
- parsing;
- extraction;
- evidence;
- graph/query;
- synthesis;
- novelty challenge;
- proposal/program;
- execution bridge.

These services use one authoritative PostgreSQL store but should not access each
other through undocumented table coupling.

## 16. Deployment shape for the first implementation

Initial development deployment:

```text
research-engine service/workers
          |
          +--> PostgreSQL 18 + pgvector
          |
          +--> content-addressed artifact directory
```

This is intentionally boring.

A single-researcher system that may ingest thousands of papers does not need a
distributed graph/vector architecture before benchmarks demonstrate that need.

## 17. Technology evidence checked 2026-09-30

PostgreSQL 18 current documentation confirms:

- native JSON/JSONB operators and SQL/JSON support;
- full-text search;
- recursive WITH queries suitable for recursive traversal.

pgvector 0.8.6 is the current released/default extension version observed during
this decision and supports exact nearest-neighbor search plus HNSW and IVFFlat
approximate indexes.

Official references:

- https://www.postgresql.org/docs/current/functions-json.html
- https://www.postgresql.org/docs/current/textsearch-intro.html
- https://www.postgresql.org/docs/18/sql-select.html
- https://github.com/pgvector/pgvector

## 18. Revisit triggers

Reconsider this architecture only after measured evidence shows one of:

- graph traversals dominate workload and recursive SQL is inadequate;
- corpus/vector volume makes PostgreSQL vector search operationally unsuitable;
- artifact volume requires distributed object storage;
- independent teams/services require separate scaling boundaries;
- analytical workloads justify a separate rebuildable OLAP projection.

Until then:

**one authoritative relational knowledge store, one content-addressed artifact
store, rebuildable text/vector/graph projections.**
