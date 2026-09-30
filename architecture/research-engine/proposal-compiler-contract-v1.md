# Research Engine Research-Program and Proposal Compiler Contract v1

Status: DRAFT CONTRACT
Parent architecture: ../automated-research-engine-v1.md
Synthesis/gap contract: synthesis-gap-contract-v1.md
Created: 2026-09-30

## 1. Purpose

This layer converts a sufficiently supported research gap into a structured
research program and, when an official funding opportunity is selected, compiles
that program into solicitation-specific proposal inputs.

It does not decide that a research direction is worth pursuing.

## 2. ResearchProgram

A ResearchProgram is a structured scientific plan containing:

- problem statement;
- research question;
- hypotheses;
- proposed contribution;
- experiment/work-package plan;
- data requirements;
- infrastructure requirements;
- baselines;
- evaluation metrics;
- falsification criteria;
- risks and mitigations;
- evidence provenance;
- cost/runtime dependencies;
- human decision state.

## 3. Gate from GapCandidate

A ResearchProgram may be drafted from a candidate for planning purposes, but it
must remain DRAFT_NOT_APPROVED unless:

1. the source GapCandidate is SUPPORTED_AS_OPEN or a human explicitly accepts the
   remaining novelty uncertainty;
2. a human explicitly approves the research direction.

A NARROWED or NEEDS_HUMAN_REVIEW gap must not silently become an approved program.

## 4. FundingOpportunity

FundingOpportunity is an adapter-normalized record for an official opportunity.

It records:

- agency/provider;
- official opportunity identifier;
- title;
- authoritative source URI;
- published/updated dates;
- deadlines;
- eligibility;
- required components;
- formatting/page constraints;
- review criteria;
- budget/duration constraints when applicable;
- retrieval timestamp;
- source hash/version when possible.

Official opportunity data, not remembered generic agency rules, is authoritative.

## 5. SolicitationRequirement

Each proposal requirement becomes a separately traceable record with:

- requirement ID;
- source opportunity;
- source locator/section;
- requirement category;
- requirement text/normalized rule;
- validation method;
- satisfaction state.

## 6. ProposalCompilation

A ProposalCompilation maps ResearchProgram content and evidence into an exact
FundingOpportunity.

It records:

- research program checkpoint;
- opportunity checkpoint;
- requirement matrix;
- section/component map;
- evidence citations;
- unresolved human inputs;
- compliance checks;
- submission gate.

## 7. Submission gate

Automated compilation is not automated submission.

A proposal may not become READY_FOR_SUBMISSION until:

- the research direction is human-approved;
- novelty uncertainty is accepted/resolved;
- an official opportunity is selected and current;
- all mandatory requirements are mapped;
- unresolved required human inputs are complete;
- a human explicitly approves submission.

## 8. Dry-run semantics

A dry run may test transformation mechanics with:

- an unapproved research program;
- no selected funding opportunity;
- placeholder proposal components.

Such an artifact must be marked NOT_FOR_SUBMISSION and may not claim compliance
with NSF or any other sponsor.

## 9. Evidence integrity

Proposal claims about prior work, expected contributions, or preliminary evidence
must map to EvidenceObjects/SynthesisArtifacts/GapCandidate records.

The compiler must distinguish:

- source-supported claim;
- proposed hypothesis;
- expected outcome;
- broader impact argument;
- unresolved assertion requiring human support.

## 10. v1 pilot

The first pilot uses the NARROWED efficient-blind-generative-outlier candidate
only to test program/proposal data flow.

The pilot is not:

- a novelty determination;
- a recommendation to pursue the topic;
- a funding recommendation;
- an NSF-compliant proposal;
- a submission artifact.
