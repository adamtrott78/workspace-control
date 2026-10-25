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
- Remote checkpoint: 92d70b6086b700bc76a9595c0cbcba8fe31e1f43
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 44fbf6107db2e554a5e276a1862c02c66ffd1ab9
- Remote verified: true

## Next safe action

Merge this exact INSUFFICIENT_BASELINE_GENERALIZATION result checkpoint, then close research-engine PR #251 unmerged and re-engage workspace-local-extract-independent-review-v1 on run 40146681400 / artifact 12581042417 / report sha256:1a0eed000053f064ec0f247ae3bc3f93583db9b2787d1ae8ec95362206a02db1. Do not redesign the cross-paper baseline before that review is durable.

## Remaining work

- Obtain independent post-result review of run 40146681400 / artifact 12581042417 / report sha256 1a0eed000053f064ec0f247ae3bc3f93583db9b2787d1ae8ec95362206a02db1 before redesigning the cross-paper baseline.
- After this result checkpoint merges, close research-engine PR #251 unmerged and do not retrigger.
- Do not select a recovery mechanism from the diagnostic-only 3-vs-1 counts because the all-nine baseline gate failed.
- If reviewer finds no blocking issue, redesign only the cross-paper teacher-blind baseline so all nine papers can instantiate the matched comparison; freeze and review that new design before implementation.
- Preserve semantic-generalization limits, rejected-family exclusions, production/Wave7B/semantic-control boundaries.

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
