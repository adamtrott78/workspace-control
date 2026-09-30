# Research Engine Synthesis and Gap Contract v1

Status: DRAFT CONTRACT
Parent architecture: ../automated-research-engine-v1.md
Evidence graph contract: evidence-graph-contract-v1.md
Created: 2026-09-30

## 1. Purpose

The synthesis/gap layer converts evidence-graph state into reproducible scientific
interpretation without allowing generated prose or novelty judgments to become
source facts.

## 2. SynthesisArtifact

A SynthesisArtifact is a generated view over an explicit evidence checkpoint.

It records:

- the question/scope;
- graph snapshot;
- input evidence IDs;
- input inference IDs;
- generated statements;
- per-statement evidence maps;
- known scope limitations;
- generator identity/version;
- timestamp.

A synthesis is staleable and reproducible.

It never replaces its input evidence.

## 3. Evidence scope

A synthesis must state how broad its evidence base is.

Suggested scope classes:

- SINGLE_WORK
- CURATED_SUBSET
- CORPUS
- SYSTEMATIC_SEARCH
- META_ANALYTIC

A SINGLE_WORK synthesis must never be phrased as a field-wide conclusion.

## 4. GapCandidate

A GapCandidate is an Inference, not a Fact.

Minimum states:

- PROPOSED
- UNDER_CHALLENGE
- NARROWED
- REJECTED_PRIOR_WORK_FOUND
- NEEDS_HUMAN_REVIEW
- SUPPORTED_AS_OPEN

The initial state is PROPOSED.

## 5. Gap motivation

Gap candidates may be motivated by:

- repeated author-stated limitations;
- conflicting evidence;
- sparse method/dataset/condition coverage;
- expensive/tuned methods;
- missing external validation;
- missing baselines;
- missing uncertainty analysis;
- stale benchmarks;
- untested combinations;
- new capabilities that make old assumptions unnecessary.

A single-paper observation may generate a candidate, but cannot validate a
field-wide gap.

## 6. Novelty challenge

Before a candidate can become SUPPORTED_AS_OPEN, the engine must search to
disprove it.

For each candidate:

1. decompose the candidate into searchable propositions;
2. search exact terminology;
3. search synonyms/adjacent terminology;
4. search recent work separately;
5. inspect nearest prior work and citation neighborhoods;
6. record counterevidence;
7. reject, narrow, or escalate the candidate.

Absence of a matching search result is not proof of novelty.

## 7. Counterevidence source levels

Novelty challenge may use metadata/abstract-level evidence to reject or narrow a
broad candidate when the prior work clearly covers the same proposition.

A candidate should require deeper reading before a subtle distinction is accepted
as novel.

## 8. Rejection rule

If a candidate says "no work addresses X" and a discovered paper's title/abstract
explicitly addresses X, the broad candidate must be REJECTED_PRIOR_WORK_FOUND or
NARROWED.

Do not rescue a broad candidate through semantic hairsplitting after prior work is
found.

## 9. First-pilot requirement

The first pilot must demonstrate at least:

- one reproducible scoped synthesis;
- one candidate gap;
- one candidate rejected by prior work;
- one candidate narrowed or escalated because counterevidence partially overlaps;
- preserved novelty-search provenance.

## 10. Acceptance boundary

No RF OSR gap from the one-paper pilot may be marked SUPPORTED_AS_OPEN.

That state requires additional corpus ingestion and deeper prior-work review.
