# Local EXTRACT Benchmark Validity Audit v0.1

Status: **DIAGNOSTICALLY USEFUL / INSUFFICIENT AS FINAL ACCEPTANCE BENCHMARK**

Owner: `workspace-research-methodology-v1`

This audit answers a narrow question:

> Does the current Local EXTRACT benchmark tell us what “solved” means, and does 13/13 teacher-atom support need to be reached?

## 1. Short answer

**No: 13/13 is not the stated success criterion for Local EXTRACT.**

The 13-atom oracle is a high-resolution diagnostic for one preserved teacher paper. It is useful for localizing retrieval/preservation failures, but it is not the full nine-paper semantic benchmark and it is not the production-promotion gate.

The current benchmark is internally coherent enough for mechanism research, but it is not sufficient by itself to establish that EXTRACT is solved across papers.

## 2. What the benchmark actually contains

The frozen Wave-1 corpus contains:

- 9 papers;
- 71 historical STANDARD Codex evidence objects;
- 43 historical evidence-bearing pages;
- 65 total PDF pages.

However, full normalized teacher claim text is preserved for only one paper:

- `arxiv:2403.04036`.

That paper has six preserved historical teacher claims (`e1` through `e6`), with `e5` duplicating the wireless-result content already represented by `e4`.

The later deterministic support oracle decomposes the unique content into **13 atoms**:

- e1.a / e1.b / e1.c
- e2.a / e2.b
- e3.a / e3.b / e3.c
- e4.a / e4.b
- e6.a / e6.b / e6.c

The oracle explicitly omits `e5.a` because it duplicates `e4.b`.

## 3. What 13/13 means

13/13 means:

> All 13 frozen semantic-support atoms selected from the preserved teacher claims of one paper are supported under the deterministic anchor oracle.

It does **not** mean:

- every scientifically useful fact in that paper was extracted;
- every historical Codex evidence object was reproduced;
- all nine papers were semantically covered;
- no unsupported or redundant claims exist;
- the local EXTRACT job is production-ready;
- Codex fallback is no longer needed.

The oracle explicitly states that the historical teacher corpus is incomplete and that absence of a teacher atom is **not** a negative label.

## 4. Is 13/13 technically reachable?

Yes.

The oracle-query diagnostic shows that under precise answer-free evidence intents:

- BGE-M3 dense reaches 13/13 within top-12;
- BGE-M3 ColBERT reaches 13/13;
- BGE-M3 hybrid reaches 13/13;
- Qwen3-Reranker-0.6B reaches 13/13;
- BGE-M3 sparse reaches 12/13;
- direct BM25 reaches 11/13.

The target-text oracle reaches 13/13 for every tested ranking arm.

Therefore the 13-atom diagnostic is not an impossible ceiling caused by missing source text. It can be saturated when the query/intent representation is sufficiently precise.

This is evidence that 13/13 is a meaningful **diagnostic ceiling on this one control**, not evidence that 13/13 should be the project-wide acceptance target.

## 5. Original Local EXTRACT success criteria

The architecture contract does not require perfection.

### Research-positive gates

- local pass precision >= 0.95
- page agreement >= 0.95
- type agreement >= 0.95
- teacher claim coverage >= 0.80
- job local-completion fraction >= 0.50

### Production-promotion gates

- all hard-safety gates pass
- local pass precision >= 0.95
- teacher claim coverage >= 0.90
- page agreement >= 0.95
- type agreement >= 0.95
- unsupported claim rate == 0 on the promotion corpus
- job local-completion fraction >= 0.80
- projected remote input-token reduction >= 0.50
- no material regression in downstream VERIFY outcome on locally completed jobs

### Longer-term adaptation target

- job local-completion fraction >= 0.90 while retaining production precision and grounding gates.

These are the actual project-level objectives.

The atom-support count is not identical to `teacher_claim_coverage`; it is a later diagnostic decomposition and must not be silently substituted for the production metric.

## 6. What current 9/13 means

The recent 9/13 result is real progress on the one-paper teacher control:

- the seven frozen control atoms remain supported;
- e1.a is recovered;
- e6.a is recovered;
- the current neighborhood-rescue case can restore those nine atoms at budget 28.

But 9/13 is **not “69% solved”**.

It is:

> 9 of 13 selected diagnostic atoms supported on the one proposition-labeled teacher paper under the current frozen evaluation.

It is valuable because it tells us mechanisms are improving while preserving known-good evidence.

It does not establish semantic generalization across the corpus.

## 7. What the nine-paper corpus currently supports

For all nine papers, durable history preserves counts and page locations.

It does not preserve normalized proposition-level teacher semantics for the other eight papers.

Therefore current cross-paper work correctly restricts itself to structural claims such as:

- whether a selected proposition can be reconstructed after a controlled origin drop;
- whether local adjacency or surviving-intent allocation is more robust;
- cost and retrieval-depth behavior;
- provenance and exact proposition identity.

The current cross-paper design explicitly forbids proposition-level semantic-generalization claims on unlabeled papers.

That is scientifically appropriate.

## 8. Benchmark weaknesses

The current benchmark has five important limitations for final acceptance.

### A. One-paper semantic teacher concentration

Only one of nine papers has proposition/claim-level teacher semantics.

This creates a major overfitting risk if architecture iterations continue to optimize the same 13 atoms.

### B. Teacher output is a comparison label, not unquestionable ground truth

The redesign contract states that preserved STANDARD Codex outputs are teacher/comparison labels. The authoritative PDF wins when teacher output and source evidence disagree.

### C. The teacher subset is incomplete

The oracle explicitly says unlisted propositions are not negatives.

Therefore standard precision/false-positive evaluation cannot be inferred from the 13-atom support set alone.

### D. Anchor support is a deterministic proxy

The 13-atom oracle uses required normalized source anchors on expected pages.

That is excellent for reproducible source-support checks but is not equivalent to a general semantic evaluator.

### E. Final success requires whole-job behavior

The project objective is mostly-local EXTRACT with rare fail-closed Codex fallback while preserving provenance, precision, completeness, downstream VERIFY behavior, and economics.

A one-paper atom score cannot measure that objective alone.

## 9. Benchmark disposition

Current disposition:

`DIAGNOSTIC_VALID_FINAL_ACCEPTANCE_INSUFFICIENT`

The current benchmark is appropriate for:

- mechanism diagnosis;
- exact source/provenance testing;
- controlled retrieval/preservation experiments;
- one-paper semantic regression controls;
- cross-paper structural robustness experiments.

It is not sufficient for:

- declaring EXTRACT solved;
- production promotion;
- claiming generalized semantic coverage;
- estimating true unsupported-claim rate across the corpus.

## 10. What is required before declaring Local EXTRACT solved

Before production acceptance, create a genuinely held-out, multi-paper semantic evaluation set.

At minimum it should include:

1. multiple papers from the nine-paper distribution or a fresh held-out corpus;
2. independently reviewed scientific evidence obligations/claims per paper;
3. exact authoritative-PDF quote/page provenance for each positive;
4. explicit adjudication of duplicate/overlapping claims;
5. a way to evaluate unsupported local claims, not only positive recall;
6. paper-level holdout from any teacher adaptation;
7. the existing production gates for precision, provenance, completion, fallback frequency, VERIFY agreement, and economics.

Historical Codex outputs can seed this benchmark, but final labels should be source-verified and versioned rather than treated as infallible truth.

## 11. Decision rule

Do **not** require 13/13 on the current teacher paper as a prerequisite to solving EXTRACT.

Do **not** accept 9/13, 12/13, or 13/13 on that paper as proof that EXTRACT is solved.

Use the 13-atom oracle as a regression/diagnostic control.

Project success should be determined by the multi-paper held-out semantic benchmark plus the original hard-safety and production-promotion gates.
