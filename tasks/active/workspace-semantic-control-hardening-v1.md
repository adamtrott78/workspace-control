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
- Remote checkpoint: b9ef0b451fec5e294c705d4886dbd828881bea05
- Remote verified: true

## Next safe action

Implement only implement_opaque_extract_socket from research-engine checkpoint b9ef0b451fec5e294c705d4886dbd828881bea05. Add pure deterministic code under prototypes/semantic_control_hardening/** and tests under tests/semantic_control_hardening/** that validates/registers FutureAcceptedExtractOutputDescriptorV1. Reject binding for unaccepted/design-only descriptors; register accepted descriptors only as metadata while keeping binding_state UNBOUND until a separate concrete adapter exists. Enforce payload_schema_opaque=true, required exact repository/commit/artifact/blob/schema identity, accepted scientific disposition/evidence, adapter_target_contract=SemanticObservationV1, and forbidden payload/prompt/model/retrieval/ontology/RDF fields. Do not define or inspect EXTRACT payload, do not mutate EXTRACT/integration/production, and do not create the final hardening verdict until this stage passes.

## Remaining work

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
