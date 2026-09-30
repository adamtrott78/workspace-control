# Research Engine Implementation Bootstrap v1

Status: TESTED LOCALLY / AWAITING REPOSITORY CREATION

The first executable implementation slice has been built and tested from the
validated architecture.

## Implemented

- PostgreSQL 18 authoritative schema;
- pgvector 0.8.6 extension boundary;
- content-addressed SHA-256 artifact store;
- typed EvidenceObject/EvidenceRelation models;
- directed relation guards;
- in-memory graph reference implementation;
- recursive provenance and claim-support SQL;
- PostgreSQL store boundary;
- mixed exact-PDF/OCR projection logic;
- exact-PDF fidelity validator;
- CLI;
- Docker Compose PostgreSQL/pgvector runtime;
- unit + PostgreSQL integration tests.

## Validation

- Python compile: PASS
- Unit tests: 6 PASS / 0 FAIL
- PostgreSQL integration test: prepared but SKIPPED in current executor because
  Docker/PostgreSQL runtime is unavailable.

The integration test initializes the real PostgreSQL schema, inserts an exact
SourceArtifact, locator, Result, Claim, and Result--SUPPORTS-->Claim relation,
then verifies the query returns the source SHA-256 and PDF page.

## Bootstrap bundle

- SHA-256: `8284f62ba73e95d7227ada42c4107c357c23992951333d4341bff4c00305161e`
- Files: 20
- Size: 9756 bytes

The bundle is recovery evidence only. The intended durable owner is
`adamtrott78/research-engine`.

## Genuine boundary

Current GitHub tooling can mutate existing repositories but cannot create one.
The current execution container also has no Docker/PostgreSQL server.

Resume when:

1. the empty `adamtrott78/research-engine` repository exists; and
2. local Docker availability has been reported.

Then populate the repository directly, run the real PostgreSQL integration test,
and continue implementation without another stop unless a new genuine boundary
or required human approval is reached.
