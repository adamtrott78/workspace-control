# Held-Out Multi-Paper Semantic Benchmark for Local EXTRACT v0.1

Status: **EXPERIMENTAL / BENCHMARK-CONSTRUCTION ONLY**

Owner: `workspace-extract-semantic-benchmark-v1`

Active EXTRACT task: read-only dependency only.

## 1. Purpose

The Local EXTRACT research program currently has a useful but narrow semantic
control: 13 deterministic evidence-support atoms derived from six historical
teacher claims on one paper.

That control is appropriate for mechanism diagnosis and regression testing, but
it is not a sufficient definition of project success.

This benchmark creates a fresh, source-verified, multi-paper semantic acceptance
surface so Local EXTRACT can eventually be judged on:

- evidence recall;
- claim precision;
- unsupported-claim rate;
- exact source provenance;
- paper-level completeness;
- fallback frequency;
- downstream VERIFY agreement;
- resource/economic impact.

The benchmark is developed in parallel with active EXTRACT research but does
not influence, mutate, or delay that research.

## 2. Data-role separation

### 2.1 Development / regression corpus

The existing nine-paper Wave-1 corpus is now **development data**.

It remains valid for:

- mechanism research;
- structural stress tests;
- exact provenance tests;
- regression checks;
- the one-paper 13-atom semantic control.

It is not eligible to establish held-out semantic generalization.

### 2.2 Annotation pilots

Two fresh papers are designated `PILOT`.

Pilot papers are used to test:

- source acquisition;
- annotation-unit granularity;
- duplicate/overlap handling;
- multi-span evidence;
- type vocabulary;
- adjudication mechanics;
- benchmark serialization.

Pilot performance never counts toward final acceptance.

### 2.3 Acceptance holdout

Eight fresh papers are designated `ACCEPTANCE`.

They are selected before Local EXTRACT is evaluated on them.

During benchmark construction:

- active EXTRACT outputs must not be generated on them;
- gold obligations must not be written from model outputs;
- acceptance labels must be source-first from authoritative PDFs.

Knowing a paper identity is not equivalent to seeing its gold labels, but the
benchmark should still avoid using the acceptance papers for architecture
debugging.

## 3. Fresh-corpus coverage goals

The fresh corpus should cover materially different evidence structures and
failure modes within the target RF/RFF distribution:

- open-set / unknown-device rejection;
- domain shift / cross-condition reliability;
- closed-set plus novel-class discovery;
- authentication / adversarial or spoofing scenarios;
- hardware anomaly / integrity detection;
- over-the-air implementation fingerprinting;
- real-world dataset / acquisition design;
- quantitative comparisons and limitations.

The benchmark is not intended to be statistically representative of all RF
research. It is a bounded acceptance set for the current Local EXTRACT research
program.

## 4. Source authority

For every paper:

1. freeze the exact source version;
2. record the authoritative PDF URL;
3. compute and freeze SHA-256;
4. record page count;
5. perform annotation against that exact PDF.

Metadata services and abstracts may be used for discovery only.

If metadata, abstract, historical teacher output, or another derived
representation disagrees with the PDF, the PDF controls.

## 5. Gold unit: evidence obligation

The primary gold unit is an **evidence obligation**.

An obligation represents one scientifically useful fact that a high-quality
EXTRACT job should be able to surface for this research distribution.

Each obligation contains:

- stable ID;
- paper/source identity;
- evidence type;
- normalized scientific claim;
- one or more exact source quotes;
- authoritative page number for every quote;
- support mode;
- importance tier;
- duplicate/overlap group when applicable;
- annotation rationale;
- adjudication state.

### 5.1 Evidence types

The initial vocabulary is:

- `METHOD`
- `DATASET_SETUP`
- `RESULT`
- `LIMITATION`
- `ROBUSTNESS_GENERALIZATION`
- `SECURITY_THREAT`
- `EVALUATION_PROTOCOL`
- `ASSUMPTION_SCOPE`

The vocabulary may be refined during pilot annotation only.

### 5.2 Support modes

- `DIRECT`: one exact quote is sufficient.
- `COMPOSITE`: two or more source spans are jointly required.
- `TABLE_OR_FIGURE_GROUNDED`: structured/visual evidence is necessary and the
  text alone is insufficient.

Composite support is explicit; one proposition is not assumed to express every
scientific obligation.

## 6. Source-first annotation protocol

Annotators must not view Local EXTRACT outputs for the paper.

For each paper:

1. read the abstract and introduction to establish contributions/scope;
2. inspect method/system description;
3. inspect dataset/experimental setup;
4. inspect main quantitative results and comparisons;
5. inspect robustness/generalization/security analyses;
6. inspect limitations/discussion/conclusion;
7. create candidate obligations from the paper itself;
8. attach exact quotes/pages;
9. merge true duplicates while retaining distinct atomic facts;
10. mark source ambiguity rather than inventing a cleaner claim.

Target density is roughly **8-15 high-value obligations per paper**, but the
count is not a quota. Scientific content controls.

No obligation is added merely to balance classes.

## 7. Importance tiers

Each obligation receives one of:

- `CORE`: central method/dataset/result/limitation needed for a competent
  research summary;
- `SECONDARY`: useful but not necessary for minimum paper comprehension.

Final primary recall is computed over CORE obligations.

Secondary obligations are reported separately and may be used for richer
completeness analysis.

This prevents the benchmark from rewarding extraction of numerous minor details
while missing the paper's central scientific content.

## 8. Independent adjudication

Final acceptance gold requires two-pass review.

### Pass A — source annotation

Creates obligations directly from the authoritative PDF.

### Pass B — blind adjudication

Reviews the PDF and Pass-A obligation set without seeing Local EXTRACT outputs.

For each obligation, Pass B may:

- `ACCEPT`
- `REWRITE_FOR_SOURCE_FIDELITY`
- `MERGE_DUPLICATE`
- `SPLIT_ATOMIC_FACTS`
- `REJECT_NOT_IMPORTANT`
- `REJECT_UNSUPPORTED`

Disagreements are resolved against the authoritative PDF.

The final gold set records annotation and adjudication provenance.

## 9. Evaluating Local EXTRACT outputs

Positive recall alone is insufficient.

For every locally emitted claim on an acceptance paper, evaluation records:

- exact quote locatability;
- page correctness;
- type correctness;
- normalized-claim support;
- relevance to the research topic;
- duplicate status;
- whether it matches one or more gold obligations.

Output classifications:

- `SUPPORTED_RELEVANT`
- `SUPPORTED_SECONDARY`
- `DUPLICATE`
- `UNSUPPORTED`
- `UNLOCATABLE`
- `OUT_OF_SCOPE`

An emitted claim does not need to match a pre-existing gold obligation to be
valid. If it is source-supported and relevant, it may count positively while
remaining outside positive-obligation recall.

This is necessary because a finite gold set cannot enumerate every valid fact.

## 10. Primary benchmark metrics

### 10.1 Semantic coverage

- per-paper CORE obligation recall;
- macro-average CORE obligation recall;
- micro-average CORE obligation recall;
- SECONDARY obligation recall;
- obligation recall by evidence type.

Macro paper recall is primary so one dense paper cannot dominate the benchmark.

### 10.2 Claim quality

- supported-relevant output precision;
- unsupported-claim rate;
- unlocatable-quote count;
- duplicate output rate;
- out-of-scope rate.

### 10.3 Provenance

- exact quote locatability;
- page agreement;
- source-span coverage.

### 10.4 Paper-level completion

A paper is locally complete only when:

- CORE obligation recall >= 0.90;
- no locally accepted claim is unsupported or unlocatable;
- page/type provenance gates pass;
- the job-local completeness audit does not request Codex fallback.

Report paper-local-completion fraction across the acceptance corpus.

### 10.5 Downstream/economics

Retain the original project metrics:

- downstream VERIFY outcome agreement;
- Codex fallback jobs/units;
- projected remote input tokens avoided;
- local wall time / VRAM / RSS;
- observed plan-allowance movement only as a separate empirical observation.

## 11. Final acceptance mapping

The benchmark does not replace the original Local EXTRACT contract.

Production promotion still requires:

- all hard-safety gates;
- local pass precision >= 0.95;
- semantic teacher/obligation coverage >= 0.90;
- page agreement >= 0.95;
- type agreement >= 0.95;
- unsupported claim rate == 0 on the promotion corpus;
- paper/job local-completion fraction >= 0.80;
- projected remote input-token reduction >= 0.50;
- no material downstream VERIFY regression.

The legacy 13-atom control remains a regression metric.

No rule requires 13/13 on that control.

## 12. Anti-overfitting / contamination rules

- The current nine-paper corpus is development-only.
- Pilot papers are never acceptance papers.
- Acceptance papers are not used for architecture debugging.
- Acceptance gold is not visible to active EXTRACT development.
- No threshold, budget, query, model, ranking rule, or prompt may be changed
  using acceptance results and then re-scored on the same frozen acceptance set
  as though still held out.
- A failed final acceptance run may motivate a new development cycle, but a new
  untouched acceptance set is required for a later unbiased promotion claim if
  material architecture tuning uses the failed holdout result.

## 13. Benchmark lifecycle

```text
fresh literature discovery
        ↓
freeze PILOT + ACCEPTANCE corpus
        ↓
freeze exact PDF identities/hashes
        ↓
pilot annotations
        ↓
validate schema/adjudication mechanics
        ↓
source-first acceptance annotation
        ↓
blind adjudication
        ↓
freeze gold
        ↓
freeze candidate EXTRACT architecture
        ↓
one acceptance evaluation
        ↓
PROMOTE / REVISE / REJECT
```

## 14. Relationship to concurrent EXTRACT research

Active EXTRACT research may continue throughout corpus construction and pilot
annotation.

The benchmark task must not:

- choose EXTRACT architecture;
- change EXTRACT gates;
- run acceptance papers through active research experiments;
- expose acceptance gold to the EXTRACT owner;
- block routine EXTRACT implementation/CI.

The first synchronization point is the eventual acceptance gate, after a
candidate EXTRACT architecture is separately frozen.
