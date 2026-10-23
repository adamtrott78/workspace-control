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
- Remote checkpoint: d6c1375c36fc3634f628392e4b1cee55b61caf12
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 265a7e4784209d411383cb09da4fe0adcf50f319
- Remote verified: true

## Next safe action

Wave 6 implementation is already merged in research-engine main at 265a7e4784209d411383cb09da4fe0adcf50f319 (PR #140, CI PASS). Bind that exact merged workflow into the existing reusable Lambda plane: add route model-eval-local-extract-wave6 with execution contract model-dual-public-v1, trusted workflow .github/workflows/lambda-ci-local-extract-wave6.yml blob c81e7cbb31f1731ada483a9b1f9256a4e6d78312, trigger /lambda-ci-local-extract-wave6, unchanged actor/open-same-repository-PR/fork-denial gates, and accepted Qwen/runtime bindings. Advance only project-manifest source identity and exact-blob regression coverage, validate/merge, require trusted reconciliation, then run exactly one inert-trigger Wave-6 benchmark. Do not modify GitRunner substrate code and do not auto-start Wave 7.

## Remaining work

- Bind merged Wave 6 into the existing research-engine project manifest as route model-eval-local-extract-wave6 using execution contract model-dual-public-v1, trusted workflow .github/workflows/lambda-ci-local-extract-wave6.yml blob c81e7cbb31f1731ada483a9b1f9256a4e6d78312, trigger /lambda-ci-local-extract-wave6, unchanged actor/open-same-repository-PR/fork-denial gates, and accepted Qwen/runtime bindings.
- Advance only project-manifest source identity and exact-blob regression coverage required by the Wave-6 route; do not modify GitRunner substrate code or execution authority.
- Validate and merge the workspace-control route change, then require trusted reconciliation before execution.
- Create/use one inert research-engine trigger PR at exact current Wave-6 main SHA 265a7e4784209d411383cb09da4fe0adcf50f319 and execute exactly one bounded Wave-6 benchmark.
- Immediately checkpoint the Wave-6 artifact, metrics, scientific disposition, and residual localization before any further experiment.
- Do not auto-start Wave 7; only after the Wave-6 decision should any next experiment, VERIFY-boundary analysis, or production integration be considered.

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
