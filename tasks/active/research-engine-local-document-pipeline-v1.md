<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-document-pipeline-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## State
- Task: `research-engine-local-document-pipeline-v1`
- Stage: `residual_escalation_and_local_semantic_fallbacks`
- research-engine remote/local canonical for this completed benchmark: `7a26e648ec409c96a3f9b7c8620f566658700894`
- research daemon: keep inactive/dead PID 0
- sustained research: disabled
- STANDARD Codex authoritative-PDF EXTRACT/VERIFY remains production semantic baseline

## PP-OCRv6 outcome
PP-OCRv6 remains resource-pass / quality-not-promoted. The content-bearing chart
was materially improved but did not establish the hard OCR quality thresholds,
and the scan/textless target proved visually almost blank and must be replaced
before scan-recovery quality can be evaluated.

## Completed PaddleOCR-VL 1.6 benchmark
The bounded direct-model run completed all three local inference calls with no
runtime exception.

Measured:
- model init: 1.4238369059967226 s
- Figure 6 first: 72.5341134469927 s
- Figure 3 warm: 108.51913859699562 s
- Figure 6 warm repeat: 72.99650769200525 s
- peak process VRAM: 19,956 MiB
- peak RSS: 2802.21484375 MiB
- warm-region max: 108.51913859699562 s

The run therefore fails the precommitted 14,336 MiB VRAM and 45 s warm-region
ceilings.

Quality review is more important than the resource miss:

- Figure 6 recovered the complete visible series/model-name inventory and did so
  consistently across the repeated run.
- However, the generated chart table collapsed the actual three-panel relations
  and fabricated many exact numeric values that are not present as authoritative
  table data in the figure. Fabricated-fact tolerance is zero.
- Figure 3 recovered many visible layer labels but flattened/conflated the three
  architecture columns and did not recover the required residual-shortcut or
  dotted-shortcut relationships.
- The current direct Transformers output is therefore useful as visual
  perception/element-recognition evidence but is **not promoted** as semantic
  authority and cannot replace EXTRACT/VERIFY.

Official PaddleOCR-VL documentation recommends its optimized official
pipeline/vLLM serving path for faster page-level parsing; the direct
Transformers path is documented as element-level recognition/text spotting.
The measured 72-108 s route is therefore not treated as the definitive parser
throughput ceiling.

## Architectural implication
The local-AI direction remains promising, but the remaining gaps should be
split into two roles:

1. cheap/specialized perception converts difficult document regions into
   structured local evidence;
2. a local semantic multimodal/text model reasons over authoritative text plus
   that evidence and must abstain/fall through when provenance or confidence is
   insufficient.

The already-prefetched `Qwen3.5-4B` is the next selected candidate because it
can directly test both sides of that boundary: visual reasoning on the same
Figure 6/Figure 3 crops and, if successful, bounded local EXTRACT/VERIFY over
authoritative source context.

Potential later specialist comparisons are limited to clear niches:
- MinerU2.5-Pro for document/page parsing;
- Granite-Docling for very cheap DocTags structure;
- DePlot/ChartGemma for chart-specific extraction/reasoning.

## Next safe action
Keep sustained research disabled and the daemon inactive/dead.

Do not continue patching the direct PaddleOCR-VL path for semantic promotion.

Open the already-prefetched Qwen3.5-4B visual fallback on the exact validated
Figure 6 and Figure 3 crops. Use explicit evidence questions and structured
outputs that directly test the durable annotated facts/relations with zero
fabricated-fact tolerance.

If Qwen3.5-4B passes visual quality/resource gates, extend it into a bounded
local EXTRACT/VERIFY calibration against contemporaneous STANDARD Codex controls
to estimate how much remote semantic throughput can be eliminated.

Do not change production routing or materialize scientific state during these
benchmarks.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route.

Treat the authoritative capsule, synchronized Markdown handoff, exact durable
Git/runtime state, and referenced research-engine evidence as the complete
handoff.

Do not rely on previous conversation state. Follow the capsule's exact
`next_safe_action`.
