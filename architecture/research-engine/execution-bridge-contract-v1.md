# Research Engine Execution Bridge Contract v1

Status: DRAFT CONTRACT
Parent architecture: ../automated-research-engine-v1.md
Proposal compiler contract: proposal-compiler-contract-v1.md
Created: 2026-09-30

## 1. Purpose

The execution bridge converts an approved ResearchProgram into deterministic
workspace-control bootstrap state so scientific execution can begin without
reconstructing the plan from a conversation.

## 2. Hard approval gate

The bridge MUST refuse project instantiation unless:

- ResearchProgram.status == APPROVED;
- the configured human approval gate is satisfied;
- required scientific/novelty conditions recorded by the program are satisfied
  or explicitly accepted by the human decision.

A DRAFT_NOT_APPROVED program may be compiled into a dry-run bootstrap plan, but
that plan must have instantiable=false.

## 3. Bridge output

An approved bridge emits a ProjectBootstrapPlan containing:

- source ResearchProgram identity/checkpoint;
- owning project repository or repository-creation requirement;
- project goal;
- project-owned scientific context to initialize;
- workspace-control task capsule payload;
- ordered work packages/stages;
- required data/infrastructure;
- baselines and metrics;
- falsification criteria;
- risk gates;
- evidence/proposal references;
- human decision history;
- exact next safe action.

## 4. Authority boundary

The bridge transfers a plan into a project; it does not move project authority
into workspace-control.

After bootstrap:

- workspace-control owns generic task/execution state;
- the project repository owns scientific methods, experiment code, datasets,
  results, analyses, and project-specific context.

## 5. Reproducibility

A ProjectBootstrapPlan must be deterministic for a fixed:

- ResearchProgram checkpoint;
- workspace-control contract checkpoint;
- selected project/repository identity;
- explicit human approval decision.

## 6. No hidden chat state

Every scientific requirement needed to start execution must be present through
durable ResearchProgram/evidence records or explicitly identified as unresolved.

## 7. Failure behavior

If approval or prerequisites are missing:

- instantiable=false;
- blockers are explicit;
- no repository mutation/project creation occurs;
- the would-be bootstrap payload may be rendered for inspection but is not
  executable.

## 8. First pilot

The current efficient-blind-generative-outlier program is DRAFT_NOT_APPROVED.

The v1 pilot therefore MUST refuse instantiation while proving that, if later
approved, its ResearchProgram can map mechanically into stages such as:

1. prior-work closure;
2. method design;
3. implementation;
4. experimental evaluation;
5. analysis/falsification;
6. publication/proposal evidence update.

This proves the bridge without selecting the research direction for the user.
