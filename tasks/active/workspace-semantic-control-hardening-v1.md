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
- Remote checkpoint: 569772c38c0166e884629494af144af826baf6c1
- Remote verified: true

## Next safe action

Implement only integrated_hardening_benchmark_and_verdict from research-engine checkpoint 569772c38c0166e884629494af144af826baf6c1. Add a deterministic benchmark runner and result contract under prototypes/semantic_control_hardening/**, benchmarks/semantic_control_hardening/**, and tests/semantic_control_hardening/**. Re-run all frozen hardening correctness/safety gates together: exact historical replay, temporal supersession/contradiction/UNKNOWN semantics, V1-V8 fail-closed outcomes with zero authorization escapes, bounded deterministic ontology slices, request-only evidence requirements with model-confidence no-op, deterministic audit-chain/tamper detection and receipt authority_effect=NONE, persisted 1k/10k/100k scale evidence integrity, and opaque EXTRACT descriptor registration behavior. Verdict must be exactly HARDENING_PASS, REVISE, or REJECT. HARDENING_PASS may be consumed later by workspace-semantic-control-integration-v1 but must not mutate that task, bind EXTRACT, or authorize production.

## Remaining work

- Run the integrated hardening benchmark across replay/temporal semantics, V1-V8 failure isolation, bounded ontology/evidence requirements, decision audit chain, persisted scale evidence, and opaque EXTRACT socket.
- Issue HARDENING_PASS, REVISE, or REJECT and durably checkpoint the result for future integration consumption.

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
