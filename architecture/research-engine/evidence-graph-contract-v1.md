# Research Engine Evidence Graph Contract v1

Status: DRAFT CONTRACT
Parent architecture: ../automated-research-engine-v1.md
Evidence contract: evidence-contract-v1.md
Extraction contract: extraction-contract-v1.md
Created: 2026-09-30

## 1. Purpose

The evidence graph is a storage-agnostic projection over canonical scholarly
identity, immutable source artifacts, source locators, typed EvidenceObjects, and
EvidenceRelations.

It is not itself the authoritative source of scientific truth.

Authority remains:

source artifact -> locator -> extracted evidence -> verified relation/inference.

The graph makes those durable records traversable.

## 2. Node identity

Graph node IDs reuse durable record IDs whenever possible.

Core node classes:

- Work
- WorkVersion
- SourceArtifact
- SourceLocator
- EvidenceObject
- Inference
- SynthesisArtifact
- GapCandidate
- ResearchProgram

The projection must not invent a second identifier namespace for records that
already have stable IDs.

## 3. Directed edge semantics

Edges are directed and must read naturally as:

`source --RELATION--> target`

Examples:

- Result --SUPPORTS--> Claim
- Limitation --QUALIFIES--> Method
- Experiment --USES--> Method
- Result --DERIVED_FROM--> Experiment
- EvidenceObject --LOCATED_AT--> SourceLocator
- EvidenceObject --EXTRACTED_FROM--> WorkVersion
- SourceArtifact --REPRESENTS--> WorkVersion
- WorkVersion --VERSION_OF--> Work

A relation whose direction does not satisfy the sentence above is invalid.

## 4. Source versus projection

The graph may contain projected convenience edges, but every projected edge must
record the durable source record(s) from which it was derived.

Deleting/rebuilding the graph must not destroy scientific evidence.

## 5. Context compatibility

Cross-paper SUPPORTS/CONTRADICTS edges must carry context compatibility.

A numeric disagreement is not automatically a contradiction.

Compatibility may consider:

- method;
- dataset/population;
- metric definition;
- operating point;
- experimental condition;
- version/time/environment.

## 6. Query contract

Every evidence-bearing query must be able to return:

1. the matching scientific object;
2. relationship path(s);
3. basis evidence IDs;
4. Work/WorkVersion identity;
5. SourceArtifact identity;
6. exact/qualified SourceLocator;
7. verification state;
8. known qualifying limitations.

A natural-language answer generated from the graph is downstream synthesis and
must not replace this trace.

## 7. Required v1 query

The first graph must answer:

> What evidence supports the paper's conclusion that generative outlier
> augmentation can reduce or replace the need to acquire physical known-outlier
> transmitters?

The answer must traverse from the conclusion Claim to supporting Results and
return their exact PDF locators and qualifying method limitations.

## 8. Database neutrality

The v1 graph contract does not select Neo4j, PostgreSQL, RDF, a document store,
or a vector database.

We first prove the object/edge/query semantics against real extracted evidence.
Only then should persistence/index technology be selected.
