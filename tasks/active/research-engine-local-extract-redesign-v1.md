<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-extract-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-extract-redesign-v1
- Title: Research Engine Mostly-Local EXTRACT Redesign v1
- Status: IN_PROGRESS
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
- Remote checkpoint: 4d580661a27f151e70f778111a88579e54de1c71
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Resume actual EXTRACT development from the Wave-1 REJECT evidence. Inspect per-paper failures in artifact 12231293963/report SHA256 5954e2de2fd1d23c770f7f687c5282b8e2f43e68c9b29ece6374fed5442f98dc, select the smallest materially different Local Evidence Agent iteration, implement it in research-engine, and execute it through the accepted Git/Lambda runner. Do not spend further work on the completed Wave-1 infrastructure support chain.

## Remaining work

- Analyze the six Wave-1 paper failures and teacher-subset disagreement to localize failure among candidate retrieval, atomic claim normalization, type assignment, confidence/guard thresholds, and completeness.
- Implement a materially different EXTRACT iteration under the accepted Local Evidence Agent architecture rather than cosmetic prompt tuning of the rejected Wave-1 normalizer.
- Use the reusable Lambda Git runner for bounded candidate-commit CPU/GPU execution; do not reopen runner infrastructure unless the execution contract itself changes.
- Measure local completion, claim-level agreement, provenance safety, fallback fraction, latency/resource use, and remote-token suppression against the preserved nine-paper baseline.
- Only after a candidate passes the semantic-quality gate consider VERIFY-boundary analysis or production integration.

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
