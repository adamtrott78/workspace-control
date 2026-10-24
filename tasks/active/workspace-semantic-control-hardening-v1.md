<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-semantic-control-hardening-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-semantic-control-hardening-v1
- Title: Semantic Control Hardening v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Harden the generic semantic-control substrate independently of the Local EXTRACT scientific task by proving historical decision replay, temporal/supersession/contradiction behavior, stale-state and version-skew failure isolation, bounded ontology-slice retrieval, generalized request-only EvidenceRequirement semantics, end-to-end DecisionEvaluation audit chains, deterministic scale behavior, and a consumer-side opaque EXTRACT integration socket. This task must improve the semantic-control infrastructure without defining, steering, implementing, or mutating EXTRACT.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 086ebf8b03dc136d733b3b9541551ea0dd99c316
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: b0abcc2b2bf8ae1630e0f149969875e32bb08ead
- Remote verified: true

## Next safe action

Implement only implement_scale_benchmark from research-engine checkpoint b0abcc2b2bf8ae1630e0f149969875e32bb08ead. Add a deterministic synthetic generator and benchmark under prototypes/semantic_control_hardening/**, benchmarks/semantic_control_hardening/**, and tests/semantic_control_hardening/** using the frozen seed 20261023 and sizes 1k/10k/100k. Measure canonical manifest rebuild, bounded ontology slice, provenance traversal, temporal replay, and decision lookup with the frozen repetition counts. Prove same seed/size gives identical manifest hash, slices remain bounded, provenance terminates on exact generated source IDs, temporal replay returns generated validity-window answers, and decision lookup has zero authorization escapes. Persist empirical min/mean/p50/p95/max; apply no pass/fail latency threshold and make no performance-promotion claim. Do not implement EXTRACT socket or production behavior yet.

## Remaining work

- Run deterministic 1k/10k/100k scale benchmarks.
- Implement and test the opaque consumer-side EXTRACT socket without defining EXTRACT payload.
- Run integrated hardening benchmark and issue HARDENING_PASS, REVISE, or REJECT.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-control-hardening-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
