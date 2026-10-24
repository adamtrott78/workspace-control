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

## Goal

Return to first principles on research-engine EXTRACT and identify, benchmark, and if justified implement a provenance-preserving mostly-local extraction architecture that makes STANDARD Codex a rare ambiguity/failure fallback rather than the default, while reusing accepted local document/VERIFY infrastructure and not repeating approaches already invalidated by durable evidence.

## Workflow

- Repository: workspace-control
- Path: workflows/evidence-first-solution-research.v1.json
- Checkpoint: a9041372c50bf1258daea2236a3e62542a115117

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 80d4bc50d4d5af550970ac4c0faa2551a15866cf
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 21c436018c9f91787d03c22174f4c4dce61ae3cb
- Remote verified: true

## Next safe action

From isolated validation implementation head f9790f4d614f022a127b5b87e33955f613159963, create an execution-envelope-only recovery that changes only `.github/workflows/local-extract-nli-certificate-validation.yml` timeout-minutes from 45 to 120. Preserve model revision/hash, SPARK/SciNLI identities, mutual-entailment scoring, max-length=1680, batch-size=16, threshold grid/calibration rule, and held-out gates exactly. Run normal CI, checkpoint the exact recovery head, then issue exactly one replacement external-only validation trigger.

## Remaining work

- Patch only workflow timeout-minutes from isolated NLI validation implementation head f9790f4d614f022a127b5b87e33955f613159963; model/data/scoring/batch/max-length/gates remain byte-for-byte or semantically unchanged.
- Run normal CI and durable-checkpoint the timeout-only recovery implementation.
- Create one inert trigger PR from the timeout-only recovery head and issue exactly one replacement `/local-extract-nli-certificate-validation <exact-trigger-head-sha>` comment.
- Observe the replacement external-only run and checkpoint NLI_CERTIFICATE_VALIDATED/PARTIAL/REJECTED with exact model/data/run/artifact/report identities.
- Only if NLI_CERTIFICATE_VALIDATED may a separate EXTRACT design substitute mutual entailment for the accepted lexical certificate; no learned EXTRACT run is authorized by validation alone.
- Do not use EXTRACT teacher labels for calibration, tune the accepted lexical threshold, train a model, start Wave 7B, change production EXTRACT/VERIFY, emit RDF/ontology output, or alter EXTRACT for semantic-control.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
