<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-extract-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-extract-redesign-v1
- Title: Research Engine Mostly-Local EXTRACT Redesign v1
- Status: CHECKPOINTED
- Capsule schema: v2
- Current stage: amr_graph_certificate_validation_result

## Goal

Return to first principles on research-engine EXTRACT and identify, benchmark, and if justified implement a provenance-preserving mostly-local extraction architecture that makes STANDARD Codex a rare ambiguity/failure fallback rather than the default, while reusing accepted local document/VERIFY infrastructure and not repeating approaches already invalidated by durable evidence.

## Current scientific result

- Recovery run: research-engine Actions run 40125779107, job 120966744810.
- Exact recovery anchor: research-engine#230@f3d30744696e5fd1e791d6ca5601f5a25950bb7d.
- Operational result: SUCCESS end-to-end; packaging repair, exact external assets, frozen scientific scoring, and report upload all passed.
- Scientific verdict: **AMR_GRAPH_CERTIFICATE_REJECTED**.
- Bio-AMR: 500/500 valid predictions; Smatch P=0.3941108851, R=0.3638515858, F1=0.3783772311, below frozen F1>=0.60.
- SPARK: no calibration threshold met frozen precision>=0.95 and recall>=0.05; selected threshold is null, which forces REJECTED.
- Artifact: 12573487854, ZIP digest `sha256:3fee9ef513429fb4a495153021b408a77ba4b753990a5172bd0277cb7f1d8fc4`.
- Scientific step runtime was about 14 minutes; runtime is additional operational evidence against using full parser+Smatch in the normal EXTRACT inner loop, but the formal rejection is from the frozen scientific gates.

## Next safe action

Merge this exact AMR scientific-result checkpoint, then close research-engine PR #230 unmerged and re-engage `workspace-local-extract-independent-review-v1` on run 40125779107 / artifact 12573487854 / verdict AMR_GRAPH_CERTIFICATE_REJECTED. Do not select or implement the next scientific architecture until that independent post-result review is durable.

## Remaining work

- Obtain an independent-review checkpoint for the exact rejected AMR result before selecting the next scientific phase.
- Close research-engine PR #230 unmerged after this checkpoint merges; do not retrigger AMR.
- Treat full AMR parser+Smatch as rejected evidence; no post-hoc threshold/model/parser/Smatch tuning to rescue it.
- After reviewer disposition, choose a materially different bounded architecture using the accumulated negative evidence rather than another cosmetic model/prompt swap.
- Preserve production EXTRACT/VERIFY and all teacher-blind / no-Wave-7B / no-semantic-control-output constraints.

## Blockers / gates

- Scientific selection gate: independent post-result review required.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
