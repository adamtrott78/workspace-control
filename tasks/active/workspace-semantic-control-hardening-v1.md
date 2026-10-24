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
- Remote checkpoint: 16150517b311b42331ce26978fbb225a760c39e2
- Remote verified: true

## Next safe action

Start only freeze_hardening_contract_and_adversaries from research-engine checkpoint 16150517b311b42331ce26978fbb225a760c39e2. Inspect the existing semantic-control prototype/integration contracts and freeze versioned historical replay cases, temporal/supersession/contradiction cases, stale-policy/task/receipt/source adversaries, bounded ontology-slice and EvidenceRequirement expected answers, deterministic 1k/10k/100k scale parameters, and FutureAcceptedExtractOutputDescriptorV1 as an opaque consumer-side descriptor. Write only benchmarks/semantic_control_hardening/** and tests/semantic_control_hardening/** in the first stage. Do not implement hardening code until those contracts and fixtures are frozen. Do not modify or define EXTRACT output.

## Remaining work

- Freeze the hardening contract, adversary fixtures, scale parameters, and opaque EXTRACT socket.
- Implement historical replay and temporal semantics.
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
