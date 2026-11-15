"""Mixed-executor Research Engine research-iterate vertical slice."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    FakeClock,
    ImmutableWorkerResultCandidate,
    InMemoryEventLedger,
    InMemoryStateStore,
    ReadOnlyRepositoryExecutor,
    RecordingTelemetry,
    RepositoryReadPostconditionValidator,
    StaticAuthorityEvaluator,
    StaticRepositoryReader,
    WorkerResultCandidateAdapter,
)
from workspace_semantic_execution.application import (  # noqa: E402
    DurableOperatorPacketMaterializer,
    ExecutorDispatchCoordinator,
    ExecutorDispatchRequest,
    ExecutorRegistry,
    OperatorActionService,
    OperatorDispatchParameters,
    PacketCompilationInput,
    PersistentExecutorSessionBroker,
    RuntimeCoordinator,
    SemanticPacketCompiler,
    TaskTreeCoordinator,
    WorkerResultIntakeService,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    AuthorityDecision,
    AuthorityOutcome,
    CandidateAction,
    DomainKernel,
    ExecutionRequirement,
    ExecutorAvailability,
    ExecutorLifecycle,
    ExecutorLocality,
    ExecutorProfile,
    InvocationMode,
    MemoryResetPolicy,
    OperatorActionState,
    PrivacyClass,
    ProcessState,
    SessionMode,
    ValidationResult,
    WorkContract,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    RepositoryFileObservation,
)


RESEARCH_ENGINE_SHA = "1031861c03b2af8cff5cf72939bbbc83a95e65a4"
SOURCE_BLOB_SHA = "0d051fa50960708e0e773f6871c7e924c5796394"
SOURCE_PATH = "src/research_engine/orchestration.py"
SOURCE_TARGET = (
    "repo://adamtrott78/research-engine@"
    f"{RESEARCH_ENGINE_SHA}/{SOURCE_PATH}"
)
FROZEN_SOURCE = (
    ROOT
    / "benchmarks"
    / "workspace-semantic-execution"
    / "backend"
    / "research-engine-1031861"
    / "orchestration.py"
)

ROOT_ID = "research-iterate"
SOURCE_ID = "research-iterate.source"
ANALYSIS_ID = "research-iterate.analysis"
SLOT_ID = "instant-general-1"
INSTANT = openai_chat_instant_current_profile()
WORKER_VALIDATOR = "validator:evidence-grounding-v1"
ROOT_CONTRACT = WorkContract(
    objective="Research the objective and synthesize a validated answer.",
    mandatory_constraints=(
        "no write-capable external effects",
        "preserve exact evidence provenance",
    ),
    provenance_refs=(f"research-engine@{RESEARCH_ENGINE_SHA}",),
    authority_refs=("scope:research-read-only",),
    validator_contracts=(WORKER_VALIDATOR,),
    output_schema_refs=("schema:research-synthesis-v1",),
)


def read_profile() -> ExecutorProfile:
    return ExecutorProfile(
        executor_id="research-engine-exact-source-read",
        provider_id="workspace-control",
        model_id="none",
        surface_id="machine",
        harness_id="repository-read-only-v1",
        toolset_id="repository-read-only",
        capabilities=frozenset({"repository.read_exact"}),
        invocation_mode=InvocationMode.DETERMINISTIC,
        session_mode=SessionMode.NONE,
        lifecycle=ExecutorLifecycle.DETERMINISTIC_PROCESS,
        memory_reset_policy=MemoryResetPolicy.NONE,
        availability=ExecutorAvailability.AVAILABLE,
        locality=ExecutorLocality.LOCAL_HOST,
        privacy_classes=frozenset(
            {PrivacyClass.PUBLIC, PrivacyClass.INTERNAL}
        ),
        resource_classes=frozenset({"CPU"}),
        scarcity_rank=0,
    )


def runtime() -> RuntimeCoordinator:
    coordinator = RuntimeCoordinator(
        state_store=InMemoryStateStore(),
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    coordinator.initialize(
        DomainKernel.create_graph(
            [
                DomainKernel.create_process(
                    ROOT_ID,
                    work_contract=ROOT_CONTRACT,
                )
            ]
        )
    )
    PersistentExecutorSessionBroker(coordinator).ensure_session(
        profile=INSTANT,
        slot_id=SLOT_ID,
        session_id="chat-research-iterate",
    )
    return coordinator


class WorkerValidator:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def validate(self, publication, packet_source):
        self.calls.append(publication.process_id)
        return ValidationResult(
            validator_id=WORKER_VALIDATOR,
            passed=True,
            evidence_ref=(
                "worker-validation:"
                f"{publication.process_id}:"
                f"{publication.source_sha256}"
            ),
            observed_at="T-validator",
        )


def packet_input(
    process_id: str,
    objective: str,
    *,
    evidence_refs=(),
) -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id=process_id,
        source_checkpoint=f"workspace-control:{process_id}",
        objective=objective,
        constraints=(
            "no write-capable external effects",
            "preserve exact evidence provenance",
        ),
        evidence_refs=tuple(evidence_refs),
        authority_refs=("scope:research-read-only",),
        allowed_actions=("publish-candidate-result",),
        validator_contract=WORKER_VALIDATOR,
        output_schema="WORKER_RESULT_V1",
        next_safe_boundary="publish immutable candidate JSON",
    )


def operator_params(
    process_id: str,
    action_id: str,
    sequence: int,
) -> OperatorDispatchParameters:
    return OperatorDispatchParameters(
        task_id="research-iterate",
        action_id=action_id,
        action_generation=0,
        worker_slot_id=SLOT_ID,
        session_generation=0,
        priority_rank=10,
        queue_sequence=sequence,
        created_at=f"T{sequence}",
        result_publication_target_ref=(
            "github-candidate://adamtrott78/workspace-control/"
            "worker-results/candidates/"
            f"{process_id.replace('.', '-')}.json"
        ),
    )


def instant_requirement() -> ExecutionRequirement:
    return ExecutionRequirement(
        required_capabilities=frozenset({"reasoning.bounded"}),
        allowed_invocation_modes=frozenset(
            {InvocationMode.HUMAN_ASSISTED}
        ),
        allowed_session_modes=frozenset(
            {SessionMode.PERSISTENT_CHAT}
        ),
        privacy_class=PrivacyClass.INTERNAL,
        require_human_launch=True,
    )


def deterministic_read_requirement() -> ExecutionRequirement:
    return ExecutionRequirement(
        required_capabilities=frozenset({"repository.read_exact"}),
        allowed_invocation_modes=frozenset(
            {InvocationMode.DETERMINISTIC}
        ),
        allowed_session_modes=frozenset({SessionMode.NONE}),
        privacy_class=PrivacyClass.INTERNAL,
        required_resource_classes=frozenset({"CPU"}),
        require_human_launch=False,
    )


def prepare_next_operator_action(
    coordinator: RuntimeCoordinator,
    action_id: str,
) -> None:
    coordinator.claim_next_operator_action(
        helper_instance_id="windows-helper",
        claim_id=f"claim:{action_id}",
        claimed_at="T-claim",
        expires_at="T-expire",
    )
    coordinator.record_operator_action_local_prepared(
        action_id=action_id,
        generation=0,
        worker_slot_id=SLOT_ID,
        session_generation=0,
        observed_at="T-prepared",
    )


def candidate_bytes(
    planned,
    *,
    kind: str,
    result_payload_ref: str | None = None,
    result_payload_sha256: str | None = None,
    reason: str | None = None,
    children=(),
) -> bytes:
    contract = planned.packet_source.result_publication
    assert contract is not None
    payload = {
        "publication_id": contract.publication_id,
        "action_id": planned.action.action_id,
        "action_generation": planned.action.generation,
        "process_id": planned.action.reasoning_process_id,
        "process_generation": planned.action.process_generation,
        "executor_id": planned.action.executor_id,
        "worker_slot_id": planned.action.worker_slot_id,
        "session_generation": planned.action.session_generation,
        "packet_sha256": planned.packet.packet_sha256,
        "kind": kind,
        "observed_at": "T-worker-result",
        "evidence_refs": [
            f"evidence:{planned.action.reasoning_process_id}"
        ],
    }
    if result_payload_ref is not None:
        payload["result_payload_ref"] = result_payload_ref
    if result_payload_sha256 is not None:
        payload["result_payload_sha256"] = result_payload_sha256
    if reason is not None:
        payload["reason"] = reason
    if children:
        payload["children"] = list(children)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def ingest_candidate(
    coordinator: RuntimeCoordinator,
    planned,
    validator: WorkerValidator,
    raw: bytes,
    *,
    revision_char: str,
):
    contract = planned.packet_source.result_publication
    assert contract is not None
    return WorkerResultCandidateAdapter(
        intake=WorkerResultIntakeService(
            runtime=coordinator,
            validators={WORKER_VALIDATOR: validator},
        )
    ).ingest(
        ImmutableWorkerResultCandidate(
            target_ref=contract.target_ref,
            immutable_revision=revision_char * 40,
            raw_bytes=raw,
        )
    )


class MixedExecutorResearchIterateTests(unittest.TestCase):
    def test_research_iterate_routes_deterministic_and_instant_then_fans_in(self):
        coordinator = runtime()
        tree = TaskTreeCoordinator(coordinator)
        worker_validator = WorkerValidator()

        observation = RepositoryFileObservation(
            repository="adamtrott78/research-engine",
            revision=RESEARCH_ENGINE_SHA,
            path=SOURCE_PATH,
            blob_id=SOURCE_BLOB_SHA,
            content=FROZEN_SOURCE.read_bytes(),
        )
        reader = StaticRepositoryReader((observation,))
        deterministic = read_profile()
        read_executor = ReadOnlyRepositoryExecutor(
            reader=reader,
            clock=FakeClock(seconds=20),
        )
        read_validator = RepositoryReadPostconditionValidator(
            reader=reader,
            clock=FakeClock(seconds=30),
        )

        source_action = CandidateAction(
            action_id="read:research-engine-orchestration",
            process_id=SOURCE_ID,
            process_generation=0,
            target_ref=SOURCE_TARGET,
            executor_type="REPOSITORY_READ_ONLY",
            idempotency_key="research-iterate:source:v1",
            preconditions=(
                "exact immutable Research Engine SHA",
                "read-only source observation",
            ),
            expected_effect="observe exact Research Engine orchestration bytes",
            postcondition_validator=(
                RepositoryReadPostconditionValidator.VALIDATOR_ID
            ),
        )
        authority = AuthorityDecision(
            decision_id="authority:research-iterate-source",
            outcome=AuthorityOutcome.ALLOW,
            action_id=source_action.action_id,
            process_id=SOURCE_ID,
            process_generation=0,
            target_ref=SOURCE_TARGET,
            authority_scope_ref="scope:research-read-only",
        )

        registry = ExecutorRegistry((deterministic, INSTANT))
        dispatcher = ExecutorDispatchCoordinator(
            runtime=coordinator,
            registry=registry,
            packet_compiler=SemanticPacketCompiler(),
            authority_evaluator=StaticAuthorityEvaluator(
                {source_action.action_id: authority}
            ),
            executor_ports={
                deterministic.executor_id: read_executor,
            },
            validators={
                RepositoryReadPostconditionValidator.VALIDATOR_ID:
                    read_validator,
            },
        )

        routing_trace = []

        root_dispatch = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=ROOT_ID,
                expected_generation=0,
                requirement_id="research-iterate:root-decompose",
                requirement=instant_requirement(),
                packet_input=packet_input(
                    ROOT_ID,
                    "Decompose the research objective into independent "
                    "evidence/source and analysis work.",
                ),
                operator=operator_params(
                    ROOT_ID,
                    "action:root-decompose",
                    1,
                ),
            )
        )
        routing_trace.append(
            root_dispatch.routing.selected_executor_id
        )
        self.assertEqual(
            root_dispatch.dispatch_mode,
            "OPERATOR_ACTION",
        )
        self.assertIsNotNone(root_dispatch.operator_dispatch)
        root_planned = root_dispatch.operator_dispatch
        assert root_planned is not None
        prepare_next_operator_action(
            coordinator,
            root_planned.action.action_id,
        )
        root_result = candidate_bytes(
            root_planned,
            kind="TOO_LARGE",
            reason="source inspection and analysis can proceed independently",
            children=(
                {
                    "process_id": SOURCE_ID,
                    "objective": (
                        "Read the exact frozen Research Engine orchestration "
                        "source and validate its immutable provenance."
                    ),
                    "provenance_refs": (
                        [f"research-engine@{RESEARCH_ENGINE_SHA}"]
                    ),
                    "authority_refs": ["scope:research-read-only"],
                    "validator_contracts": [
                        RepositoryReadPostconditionValidator.VALIDATOR_ID
                    ],
                    "output_schema_refs": ["schema:exact-source-observation-v1"],
                },
                {
                    "process_id": ANALYSIS_ID,
                    "objective": (
                        "Analyze the frozen workflow structure and identify "
                        "the synthesis-relevant constraints."
                    ),
                    "provenance_refs": (
                        [f"research-engine@{RESEARCH_ENGINE_SHA}"]
                    ),
                    "validator_contracts": [WORKER_VALIDATOR],
                    "output_schema_refs": ["schema:analysis-result-v1"],
                },
            ),
        )
        root_outcome = ingest_candidate(
            coordinator,
            root_planned,
            worker_validator,
            root_result,
            revision_char="1",
        )
        self.assertEqual(
            root_outcome.process_state,
            ProcessState.WAITING_DEPENDENCIES,
        )

        source_contract = coordinator.snapshot().graph.processes[
            SOURCE_ID
        ].work_contract
        analysis_contract = coordinator.snapshot().graph.processes[
            ANALYSIS_ID
        ].work_contract
        for contract in (source_contract, analysis_contract):
            self.assertIsNotNone(contract)
            assert contract is not None
            self.assertIn(
                "no write-capable external effects",
                contract.mandatory_constraints,
            )
            self.assertIn(
                f"research-engine@{RESEARCH_ENGINE_SHA}",
                contract.provenance_refs,
            )
            self.assertIn(
                "scope:research-read-only",
                contract.authority_refs,
            )

        source_dispatch = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=SOURCE_ID,
                expected_generation=0,
                requirement_id="research-iterate:source",
                requirement=deterministic_read_requirement(),
                packet_input=PacketCompilationInput(
                    process_id=SOURCE_ID,
                    source_checkpoint=(
                        f"research-engine@{RESEARCH_ENGINE_SHA}"
                    ),
                    objective=(
                        "Observe the exact immutable Research Engine "
                        "orchestration source."
                    ),
                    constraints=("read-only exact source",),
                    evidence_refs=(SOURCE_TARGET,),
                    authority_refs=("scope:research-read-only",),
                    allowed_actions=("read-exact-source",),
                    validator_contract=(
                        RepositoryReadPostconditionValidator.VALIDATOR_ID
                    ),
                    output_schema="schema:exact-source-observation-v1",
                    next_safe_boundary="return independently validated receipt",
                ),
                worker_id="deterministic-source-reader",
                lease_id="lease:source",
                candidate_action=source_action,
            )
        )
        routing_trace.append(
            source_dispatch.routing.selected_executor_id
        )
        self.assertEqual(
            source_dispatch.dispatch_mode,
            "DETERMINISTIC_EFFECT",
        )
        self.assertIsNotNone(source_dispatch.coordinated_result)
        source_result = source_dispatch.coordinated_result
        assert source_result is not None
        self.assertTrue(source_result.completed)
        self.assertTrue(source_result.validation.passed)
        self.assertIn(SOURCE_BLOB_SHA, source_result.validation.evidence_ref)

        tree.refresh_fan_in(event_id="source-complete")
        self.assertEqual(
            coordinator.snapshot().graph.processes[ROOT_ID].state,
            ProcessState.WAITING_DEPENDENCIES,
        )

        analysis_dispatch = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=ANALYSIS_ID,
                expected_generation=0,
                requirement_id="research-iterate:analysis",
                requirement=instant_requirement(),
                packet_input=packet_input(
                    ANALYSIS_ID,
                    "Analyze the Research Engine workflow structure using "
                    "the exact frozen provenance.",
                    evidence_refs=(source_result.validation.evidence_ref,),
                ),
                operator=operator_params(
                    ANALYSIS_ID,
                    "action:analysis",
                    2,
                ),
            )
        )
        routing_trace.append(
            analysis_dispatch.routing.selected_executor_id
        )
        self.assertIsNotNone(analysis_dispatch.operator_dispatch)
        analysis_planned = analysis_dispatch.operator_dispatch
        assert analysis_planned is not None
        prepare_next_operator_action(
            coordinator,
            analysis_planned.action.action_id,
        )
        analysis_outcome = ingest_candidate(
            coordinator,
            analysis_planned,
            worker_validator,
            candidate_bytes(
                analysis_planned,
                kind="RESULT",
                result_payload_ref=(
                    "github://research-iterate-analysis@immutable"
                ),
                result_payload_sha256="a" * 64,
            ),
            revision_char="2",
        )
        self.assertEqual(
            analysis_outcome.process_state,
            ProcessState.COMPLETED,
        )

        tree.refresh_fan_in(event_id="analysis-complete")
        resumed_root = coordinator.snapshot().graph.processes[ROOT_ID]
        self.assertEqual(
            resumed_root.state,
            ProcessState.READY_TO_RESUME,
        )

        source_receipt = next(
            iter(
                coordinator.snapshot().graph.processes[
                    SOURCE_ID
                ].effect_receipts.values()
            )
        )
        analysis_receipt = next(
            iter(
                coordinator.snapshot().graph.processes[
                    ANALYSIS_ID
                ].effect_receipts.values()
            )
        )
        synthesis_dispatch = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=ROOT_ID,
                expected_generation=0,
                requirement_id="research-iterate:synthesis",
                requirement=instant_requirement(),
                packet_input=packet_input(
                    ROOT_ID,
                    "Synthesize the validated exact-source and analysis "
                    "results into the final research answer.",
                    evidence_refs=(
                        source_result.validation.evidence_ref,
                        source_receipt.target_ref,
                        analysis_receipt.target_ref,
                    ),
                ),
                operator=operator_params(
                    ROOT_ID,
                    "action:root-synthesis",
                    3,
                ),
            )
        )
        routing_trace.append(
            synthesis_dispatch.routing.selected_executor_id
        )
        synthesis_planned = synthesis_dispatch.operator_dispatch
        self.assertIsNotNone(synthesis_planned)
        assert synthesis_planned is not None
        prepare_next_operator_action(
            coordinator,
            synthesis_planned.action.action_id,
        )
        final = ingest_candidate(
            coordinator,
            synthesis_planned,
            worker_validator,
            candidate_bytes(
                synthesis_planned,
                kind="RESULT",
                result_payload_ref=(
                    "github://research-iterate-synthesis@immutable"
                ),
                result_payload_sha256="f" * 64,
            ),
            revision_char="3",
        )

        self.assertEqual(final.process_state, ProcessState.COMPLETED)
        graph = coordinator.snapshot().graph
        self.assertEqual(
            graph.processes[ROOT_ID].state,
            ProcessState.COMPLETED,
        )
        self.assertEqual(
            graph.operator_actions[
                "action:root-synthesis"
            ].status,
            OperatorActionState.COMPLETED,
        )
        self.assertEqual(
            graph.executor_sessions[SLOT_ID].state.value,
            "READY",
        )
        self.assertEqual(
            routing_trace,
            [
                INSTANT.executor_id,
                deterministic.executor_id,
                INSTANT.executor_id,
                INSTANT.executor_id,
            ],
        )
        self.assertNotIn(
            "institutional-llm-unprovisioned",
            routing_trace,
        )
        self.assertEqual(reader.read_count, 2)
        self.assertEqual(
            worker_validator.calls,
            [ANALYSIS_ID, ROOT_ID],
        )


if __name__ == "__main__":
    unittest.main()
