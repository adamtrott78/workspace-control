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
- Remote checkpoint: f2c5fa6ac448196c908ef6e8bd35552c62653527
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 315d73e3c2f17902d228430f8b13ece002d487c9
- Remote verified: true

## Next safe action

Create exactly one inert research-engine trigger PR from timeout-recovery head 443a03ce84508859f18129aee3cad1bd703e295c, then issue exactly one replacement `/local-extract-nli-certificate-validation <exact-trigger-head-sha>` comment. Observe the unique replacement external-only run under the 120-minute execution envelope and evaluate only frozen NLI_CERTIFICATE_VALIDATED/PARTIAL/REJECTED. Checkpoint exact model/data/run/artifact/report identities and close the trigger PR unmerged. No additional replacement run is authorized by this capsule.

## Remaining work

- Create one inert research-engine trigger PR from exact timeout-recovery head 443a03ce84508859f18129aee3cad1bd703e295c.
- Issue exactly one replacement `/local-extract-nli-certificate-validation <exact-trigger-head-sha>` comment; no further rerun is authorized by the current capsule.
- Observe the replacement external-only validation run and checkpoint NLI_CERTIFICATE_VALIDATED/PARTIAL/REJECTED with exact model/data/run/artifact/report identities.
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
