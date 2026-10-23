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
- Remote checkpoint: f8ef39e9a9ff394491590448725689fa9cb0eb16
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: dcdcfc8c85ddda2bfbf8fe439c79a8e0784ee276
- Remote verified: true

## Next safe action

On research-engine inert PR #178, verify head SHA dcdcfc8c85ddda2bfbf8fe439c79a8e0784ee276 and then issue exactly one comment: /lambda-ci-local-extract-wave7a3 dcdcfc8c85ddda2bfbf8fe439c79a8e0784ee276. Observe only the resulting run. Do not issue a duplicate trigger, do not merge the trigger PR, do not change the frozen Wave 7A.3 scientific contract, and do not start Wave 7B.

## Remaining work

- Issue exactly one /lambda-ci-local-extract-wave7a3 dcdcfc8c85ddda2bfbf8fe439c79a8e0784ee276 comment on open inert PR #178; do not mutate its head and do not merge it.
- Observe the resulting corrected Wave 7A.3 run under the original frozen contract. If it returns INVALID_IMPLEMENTATION, keep scientific_gate_consumed=false and repair only demonstrated execution validity. If it reaches PROMISING/PARTIAL/REJECT, treat that as the single valid scientific disposition.
- Checkpoint the corrected run artifact/hashes, implementation-validity status, control metrics, and scientific disposition immediately in research-engine and this task capsule; then close PR #178 unmerged.
- Do not begin Wave 7B and do not change production STANDARD Codex EXTRACT or accepted page-scoped Qwen VERIFY.

## Blockers / gates

- Exactly one corrected Wave 7A.3 scientific trigger is authorized on inert PR #178 at exact head dcdcfc8c85ddda2bfbf8fe439c79a8e0784ee276. After that comment is issued, do not issue any duplicate trigger while its run is queued or running.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
