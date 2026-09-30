# Course content-ingestion procedure

## Purpose

Preserve source evidence and create a provenance-aware semantic representation
using the modality appropriate to the source.

The course repository owns source authority, provenance, synthesis destinations,
and promotion into cumulative state.

## Procedure

1. **Repository-first identity lookup.** If an exact source identity already has
   a complete durable representation, verified re-entry may be a no-op.
2. **Preserve original evidence.** Retain original images/PDFs/messages as
   required before relying on derivatives.
3. **Choose modality appropriately.** Prefer direct multimodal interpretation for
   readable classroom photos, whiteboards, handwriting, diagrams, or mixed
   visual layouts; native text parsing for text-native sources; OCR/Mathpix only
   when it materially improves transcription/retrieval; verify damaged OCR
   against native evidence.
4. **Synthesize.** Distinguish source-supported content, derived transcription,
   recollection/reference explanation, and uncertainty.
5. **Validate provenance.** Check project-required identity/version/order/hash
   and preserve discrepancies.
6. **Promote deliberately.** Write semantic knowledge only through the
   project-owned destination. Ingestion does not imply mastery.

## Idempotency and gates

Use exact source identity as an idempotency key when available. Paid OCR,
unavailable private bytes, destructive source replacement, or an explicit
project human-review rule may gate work; visual evidence alone does not.
