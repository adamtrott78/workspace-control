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
- Remote checkpoint: 5e0496b76aa004c97d281265dc045a49007b4806
- Remote verified: true

## Next safe action

Implement only implement_historical_replay_and_temporal_semantics from research-engine checkpoint 5e0496b76aa004c97d281265dc045a49007b4806. Add pure deterministic code under prototypes/semantic_control_hardening/** and tests under tests/semantic_control_hardening/**. Reproduce frozen R1/R2/R3 historical decisions from pinned historical authority/candidate/precondition inputs while ignoring divergent current state; implement temporal replay for supersession intervals, contradiction preservation, and UNKNOWN semantics. No version-skew enforcement, ontology slicing, scale work, EXTRACT binding, external runtime, or production mutation yet.

## Remaining work

- Implement historical decision replay and temporal/supersession/contradiction semantics.
- Implement version-skew/failure-isolation hardening.
- Implement bounded ontology slicing and generalized request-only evidence requirements.
- Implement decision audit chains and receipt-reference validation.
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
