<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-document-pipeline-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-document-pipeline-v1
- Title: Research Engine Local Document Intelligence and Compute Offload v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, benchmark, and integrate a provenance-preserving local document-intelligence pipeline that converts content-addressed research PDFs into reusable LLM-ready paper packages, minimizes paid/plan semantic usage and repeated PDF interpretation, and systematically evaluates every research-engine stage for safe deterministic or local-model offload before production deployment on the Lambda.

## Current stage

candidate_parser_bakeoff

## Validated so far

- Whole-pipeline localization inventory and `paper-package.v1` contract are validated.
- Seven-paper / 73-page Mathpix seed is active; original PDFs remain authoritative.
- Native pypdf baseline is canonical.
- Isolated Docling/MinerU/Paddle/Marker runtime contracts are canonical.
- Successful Lambda cheap-path bakeoff: Docling/native advanced; MinerU `flash_native` current configuration was rejected as noncompetitive.
- Docling native result: 73 pages in 10.761208 s, 55,862 tokens vs Mathpix 56,191, mean text/order agreement 0.9250/0.8836.
- DoclingDocument -> `paper-package.v1` structured normalizer is canonical at research-engine `01797e7a3d0805f02afc7a348125420663623956`; PR and canonical-main CI are green.
- Successful raw bakeoff output is preserved at `/home/atrott/adamArchives/Adam/.workspace-control/tmp/document-native-fast-20261002T012639Z`.

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On the Lambda, verify the research-engine checkout is clean on main@9e343436ccda56c08936855b48079302f7470e0a, fetch origin, verify canonical commit 01797e7a3d0805f02afc7a348125420663623956 is present and descends from the current checkout, then fast-forward exactly to that commit. Run bash deploy/run-docling-structured-normalization.sh /home/atrott/adamArchives/Adam/.workspace-control/tmp/document-native-fast-20261002T012639Z and preserve the complete terminal output plus the generated docling-normalization-summary.json. This replay reuses the existing successful Docling structured JSONs and must not rerun Docling, MinerU, or any model-backed parser. Keep the daemon inactive/dead throughout.

## Remaining work

- On the stopped Lambda, fast-forward clean research-engine main from 9e343436ccda56c08936855b48079302f7470e0a exactly to 01797e7a3d0805f02afc7a348125420663623956.
- Run deploy/run-docling-structured-normalization.sh against /home/atrott/adamArchives/Adam/.workspace-control/tmp/document-native-fast-20261002T012639Z; do not rerun Docling or MinerU.
- Evaluate real seven-paper paper-package.v1 outputs: body-item provenance coverage, bbox coverage, caption coverage, text/order agreement, table/formula/picture count agreement, warnings and any fail-closed cases.
- After successful replay, implement deterministic figure/image materialization and content-aware structure fidelity tests rather than relying only on count agreement.
- Run pypdf plain on the same Lambda for controlled throughput/resource comparison.
- Then begin non-materializing EXTRACT/VERIFY A/B using paper-package.v1 before any production integration.
- Only if native paths fail specific document classes should heavier Docling/Marker/Paddle/MinerU tiers be benchmarked.

## Blockers / gates

- The canonical Docling structured normalizer has not yet been replayed against the seven real Lambda Docling JSON outputs.
- Figure image materialization remains deliberately deferred; current normalization retains FIGURE blocks and caption/provenance metadata without claiming image assets.
- Structure-count agreement is only a coarse diagnostic and is not equivalent to equation/table/figure content fidelity.
- A same-Lambda pypdf plain benchmark is still needed before comparing native throughput directly across pypdf and Docling.
- Scanned/malformed-text cases and heavier local-model tiers remain unvalidated.
- Research daemon must remain inactive/dead throughout normalization replay.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's exact next_safe_action.
Keep research-engine-daemon.service inactive/dead unless the capsule explicitly opens a bounded runtime gate.
Mathpix is benchmark/reference only; do not add a paid Mathpix API dependency.
Do not rerun the successful native parsers for the next step; normalize the preserved Docling structured JSONs.
Do not install heavier Docling/Marker/Paddle/MinerU tiers before the structured-native replay is evaluated.
Every fresh-chat initialization or handoff prompt for this task must include the full workspace-control repository URL shown above.
