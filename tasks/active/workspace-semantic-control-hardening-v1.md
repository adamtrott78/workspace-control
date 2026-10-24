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
- Remote checkpoint: 57517d5b73275c07321d05a5ae731ff3e1001e92
- Remote verified: true

## Next safe action

Implement only implement_decision_audit_chain from research-engine checkpoint 57517d5b73275c07321d05a5ae731ff3e1001e92. Add pure deterministic code under prototypes/semantic_control_hardening/** and tests under tests/semantic_control_hardening/**. Build an audit-chain record that binds candidate_action_id, semantic_manifest_id, knowledge_checkpoint_ids, exact authority context/source identity, precondition evidence, DecisionEvaluation decision/reasons, and an optional later execution receipt reference. Validate receipt identity against candidate/evaluation without giving receipts authority. Prove exact chain hashing/reconstruction, historical replay compatibility, missing/mismatched receipt fail-closed labeling, and no fabricated receipt when none exists. Do not implement scale or EXTRACT socket yet.

## Remaining work

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
