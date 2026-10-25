# EXTRACT Semantic Benchmark Adjudication Protocol v0.1

Status: **PILOT-VALIDATION PROTOCOL**

Owner: `workspace-extract-semantic-benchmark-v1`

## Purpose

This protocol converts source-first paper annotations into a stable acceptance
gold set without consulting Local EXTRACT outputs.

## Roles

### Pass A — source annotator

The source annotator reads the authoritative PDF and proposes evidence
obligations.

The annotator must not:

- view Local EXTRACT outputs for that paper;
- optimize obligation wording around known retrieval/query behavior;
- use historical Codex output as ground truth;
- infer unsupported detail from general domain knowledge.

### Pass B — adjudicator

The adjudicator reads the same authoritative PDF plus Pass-A obligations.

The adjudicator must remain blind to Local EXTRACT outputs and may classify each
obligation as:

- `ACCEPT`
- `REWRITE_FOR_SOURCE_FIDELITY`
- `MERGE_DUPLICATE`
- `SPLIT_ATOMIC_FACTS`
- `REJECT_NOT_IMPORTANT`
- `REJECT_UNSUPPORTED`

The adjudicator may add a missed CORE obligation only when it is independently
identified from the paper, with source provenance.

## Atomicity

An obligation should express one decision-relevant scientific fact.

Prefer splitting when independently useful facts could be recovered separately,
for example:

- method + quantitative result;
- dataset size + collection environment;
- two unrelated limitations.

Keep one obligation when several source spans are jointly necessary to support a
single scientific conclusion.

## CORE / SECONDARY

Mark `CORE` when omitting the fact would materially distort a competent
research summary of the paper.

Typical CORE content:

- central mechanism;
- principal dataset/test setup;
- headline quantitative result;
- major robustness/generalization result;
- explicit limitation that materially bounds applicability.

Use `SECONDARY` for useful but nonessential detail.

Do not assign importance to manufacture a target class balance.

## Duplicates and overlap

Two obligations are duplicates when satisfying either one necessarily satisfies
the other without additional scientific information.

Related but distinct facts are not duplicates.

Examples:

- “93% cross-day accuracy” and “95% cross-location accuracy” are distinct
  robustness claims.
- A grouped claim that repeats those same two metrics adds no independent
  obligation and should be merged.

Every duplicate cluster gets a stable `duplicate_group`.

## Provenance

Final gold uses:

- exact authoritative PDF identity/hash;
- 1-based PDF page number;
- deterministic canonical page-text extraction identity;
- canonical span SHA-256;
- short anchor excerpt for navigation.

The full quoted passage need not be committed to Git.

For table/figure-grounded evidence, record the page and structured/visual object
identity. Do not fabricate a text-only quote when the result genuinely depends
on a table or figure.

## Source ambiguity

If the paper itself is ambiguous:

- preserve the ambiguity;
- reduce claim strength;
- or reject the obligation.

Do not repair a paper's wording using outside knowledge.

## Output-evaluation adjudication

When the final candidate EXTRACT system is evaluated, each locally emitted claim
is classified independently of whether it matches a gold obligation:

- `SUPPORTED_RELEVANT`
- `SUPPORTED_SECONDARY`
- `DUPLICATE`
- `UNSUPPORTED`
- `UNLOCATABLE`
- `OUT_OF_SCOPE`

This prevents the finite positive gold set from incorrectly treating every
unlisted but valid fact as a false positive.

An output can therefore be source-valid without increasing gold-obligation
recall.

## Completion rule

A paper is locally complete only if:

- CORE obligation recall >= 0.90;
- no locally accepted claim is `UNSUPPORTED` or `UNLOCATABLE`;
- provenance/type gates pass;
- the Local EXTRACT completeness controller does not request fallback.

## Disagreement log

Every Pass-A / Pass-B disagreement should record:

- original obligation ID;
- disputed field;
- annotator position;
- adjudicator position;
- final resolution;
- authoritative PDF evidence identity.

The disagreement log is benchmark-quality evidence and should be retained.

## Acceptance-gold freeze

After adjudication:

1. compute a canonical gold JSON hash;
2. record source PDF hashes;
3. mark the paper `GOLD_FROZEN`;
4. prohibit further changes before the one-shot acceptance evaluation.

Any post-evaluation gold correction must be classified separately as benchmark
repair and cannot be used to retroactively turn a failed system result into a
pass without a fresh acceptance run and contamination review.
