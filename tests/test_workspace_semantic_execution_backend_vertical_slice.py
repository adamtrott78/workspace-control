"""Coordinated Research Engine read-only vertical-slice acceptance tests."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    FakeClock,
    InMemoryEventLedger,
    InMemoryStateStore,
    ReadOnlyRepositoryExecutor,
    RecordingTelemetry,
    RepositoryReadPostconditionValidator,
    StaticAuthorityEvaluator,
    StaticRepositoryReader,
)
from workspace_semantic_execution.application import (  # noqa: E402
    CoordinatedActionService,
    CoordinatedExecutionError,
    CoordinatedExecutionRequest,
    ExecutorRegistry,
    PacketCompilationInput,
    SemanticPacketCompiler,
    RuntimeCoordinator,
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
    PrivacyClass,
    ProcessState,
    SessionMode,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    RepositoryFileObservation,
    RepositoryReadRequest,
)


RESEARCH_ENGINE_SHA = "1031861c03b2af8cff5cf72939bbbc83a95e65a4"
SOURCE_BLOB_SHA = "0d051fa50960708e0e773f6871c7e924c5796394"
SOURCE_PATH = "src/research_engine/orchestration.py"
TARGET_REF = (
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
PROCESS_ID = "re:v1:observe-orchestration"


def executor_profile() -> ExecutorProfile:
    return ExecutorProfile(
        executor_id="research-engine-exact-read",
        provider_id="repository-port",
        model_id="none",
        surface_id="machine",
        harness_id="research-engine-coordinated-read-v1",
        toolset_id="repository-read-only",
        capabilities=frozenset({"repository.read_exact"}),
        invocation_mode=InvocationMode.DETERMINISTIC,
        session_mode=SessionMode.NONE,
        lifecycle=ExecutorLifecycle.DETERMINISTIC_PROCESS,
        memory_reset_policy=MemoryResetPolicy.NONE,
        availability=ExecutorAvailability.AVAILABLE,
        locality=ExecutorLocality.LOCAL_HOST,
        privacy_classes=frozenset({PrivacyClass.PUBLIC}),
        resource_classes=frozenset({"CPU"}),
        scarcity_rank=0,
        human_launch_required=False,
    )


def execution_requirement(
    *,
    capability: str = "repository.read_exact",
) -> ExecutionRequirement:
    return ExecutionRequirement(
        required_capabilities=frozenset({capability}),
        allowed_invocation_modes=frozenset(
            {InvocationMode.DETERMINISTIC}
        ),
        allowed_session_modes=frozenset({SessionMode.NONE}),
        allowed_lifecycles=frozenset(
            {ExecutorLifecycle.DETERMINISTIC_PROCESS}
        ),
        allowed_memory_reset_policies=frozenset(
            {MemoryResetPolicy.NONE}
        ),
        allowed_localities=frozenset({ExecutorLocality.LOCAL_HOST}),
        privacy_class=PrivacyClass.PUBLIC,
        required_resource_classes=frozenset({"CPU"}),
        require_human_launch=False,
    )


def packet_input() -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id=PROCESS_ID,
        source_checkpoint=f"research-engine@{RESEARCH_ENGINE_SHA}",
        objective=(
            "Observe the exact Research Engine orchestration source so the "
            "semantic execution backend can validate the pinned workflow shape."
        ),
        constraints=(
            "Research Engine is read-only.",
            "Use only the exact immutable source revision.",
            "No model inference is required.",
        ),
        evidence_refs=(
            f"git-blob:{SOURCE_BLOB_SHA}",
        ),
        authority_refs=(
            "scope:research-engine-exact-source-read",
        ),
        allowed_actions=("repository.read_exact",),
        validator_contract=(
            RepositoryReadPostconditionValidator.VALIDATOR_ID
        ),
        next_safe_boundary=(
            "Stop after independently validating the exact immutable read."
        ),
    )


def candidate(*, generation: int = 0) -> CandidateAction:
    return CandidateAction(
        action_id="re:v1:read-orchestration",
        process_id=PROCESS_ID,
        process_generation=generation,
        target_ref=TARGET_REF,
        executor_type=ReadOnlyRepositoryExecutor.EXECUTOR_TYPE,
        idempotency_key="re:v1:read-orchestration",
        preconditions=(
            "exact immutable Research Engine revision",
            "read-only effect",
        ),
        expected_effect="observe exact Research Engine orchestration bytes",
        postcondition_validator=(
            RepositoryReadPostconditionValidator.VALIDATOR_ID
        ),
    )


def allow_decision(*, generation: int = 0) -> AuthorityDecision:
    return AuthorityDecision(
        decision_id="authority:re:v1:exact-read",
        outcome=AuthorityOutcome.ALLOW,
        action_id=candidate().action_id,
        process_id=PROCESS_ID,
        process_generation=generation,
        target_ref=TARGET_REF,
        authority_scope_ref="scope:research-engine-exact-source-read",
    )


def observation(*, content: bytes | None = None) -> RepositoryFileObservation:
    return RepositoryFileObservation(
        repository="adamtrott78/research-engine",
        revision=RESEARCH_ENGINE_SHA,
        path=SOURCE_PATH,
        blob_id=SOURCE_BLOB_SHA,
        content=FROZEN_SOURCE.read_bytes() if content is None else content,
    )


class SequencedReader:
    def __init__(self, observations):
        self._observations = tuple(observations)
        self.read_count = 0

    def read_exact(
        self,
        request: RepositoryReadRequest,
    ) -> RepositoryFileObservation:
        item = self._observations[
            min(self.read_count, len(self._observations) - 1)
        ]
        self.read_count += 1
        return item


def make_runtime():
    store = InMemoryStateStore()
    ledger = InMemoryEventLedger()
    clock = FakeClock()
    telemetry = RecordingTelemetry()
    runtime = RuntimeCoordinator(
        state_store=store,
        event_ledger=ledger,
        telemetry=telemetry,
        clock=clock,
    )
    runtime.initialize(
        DomainKernel.create_graph(
            [DomainKernel.create_process(PROCESS_ID)]
        )
    )
    return runtime, clock, telemetry


def make_service(
    *,
    reader,
    authority_evaluator=None,
    registry=None,
):
    runtime, clock, telemetry = make_runtime()
    profile = executor_profile()
    registry = registry or ExecutorRegistry((profile,))
    authority_evaluator = authority_evaluator or StaticAuthorityEvaluator(
        {candidate().action_id: allow_decision()}
    )
    executor = ReadOnlyRepositoryExecutor(reader=reader, clock=clock)
    validator = RepositoryReadPostconditionValidator(
        reader=reader,
        clock=clock,
    )
    service = CoordinatedActionService(
        runtime=runtime,
        registry=registry,
        packet_compiler=SemanticPacketCompiler(),
        authority_evaluator=authority_evaluator,
        executor_ports={profile.executor_id: executor},
        validators={
            RepositoryReadPostconditionValidator.VALIDATOR_ID: validator
        },
    )
    return service, runtime, telemetry, executor


def request(
    *,
    requirement=None,
    generation: int = 0,
) -> CoordinatedExecutionRequest:
    return CoordinatedExecutionRequest(
        process_id=PROCESS_ID,
        worker_id="coordinated-read-worker",
        lease_id=f"coordinated-read-lease-{generation}",
        expected_generation=generation,
        requirement_id="re:v1:exact-read-requirement",
        requirement=requirement or execution_requirement(),
        packet_input=packet_input(),
        candidate_action=candidate(generation=generation),
    )


class CoordinatedResearchEngineReadOnlySliceTests(unittest.TestCase):
    def test_exact_research_engine_slice_completes_only_after_validation(self):
        reader = StaticRepositoryReader((observation(),))
        service, runtime, telemetry, executor = make_service(reader=reader)

        result = service.execute(request())

        self.assertTrue(result.completed)
        self.assertTrue(result.validation.passed)
        self.assertEqual(
            result.final_snapshot.graph.processes[PROCESS_ID].state,
            ProcessState.COMPLETED,
        )
        self.assertEqual(
            result.routing.selected_executor_id,
            "research-engine-exact-read",
        )
        self.assertEqual(result.executor.invocation_mode, InvocationMode.DETERMINISTIC)
        self.assertEqual(result.authority.outcome, AuthorityOutcome.ALLOW)
        self.assertEqual(
            result.action.authority_scope_ref,
            "scope:research-engine-exact-source-read",
        )
        self.assertEqual(result.receipt.generation, 0)
        self.assertEqual(len(result.packet.packet_sha256), 64)
        self.assertEqual(reader.read_count, 2)
        self.assertEqual(len(executor.observations), 1)

        event_names = [record.name for record in telemetry.records]
        self.assertEqual(
            event_names,
            [
                "runtime.initialized",
                "process.claimed",
                "process.started",
                "process.effect_recorded",
                "process.terminal_proposed",
                "process.validation_started",
                "process.validation_recorded",
            ],
        )
        self.assertEqual(runtime.snapshot().version, 6)

    def test_packet_hash_is_reproducible_from_same_typed_state(self):
        compiler = SemanticPacketCompiler()
        profile = executor_profile()

        first = compiler.compile(packet_input(), executor=profile)
        second = compiler.compile(packet_input(), executor=profile)

        self.assertEqual(first.packet_sha256, second.packet_sha256)
        self.assertEqual(
            first.canonical_payload_json,
            second.canonical_payload_json,
        )
        self.assertEqual(first.text, second.text)

    def test_unknown_authority_produces_no_effect_or_state_transition(self):
        reader = StaticRepositoryReader((observation(),))
        service, runtime, _telemetry, executor = make_service(
            reader=reader,
            authority_evaluator=StaticAuthorityEvaluator(),
        )

        with self.assertRaisesRegex(
            CoordinatedExecutionError,
            "authority_not_allow:UNKNOWN",
        ):
            service.execute(request())

        process = runtime.snapshot().graph.processes[PROCESS_ID]
        self.assertEqual(process.state, ProcessState.READY)
        self.assertEqual(process.generation, 0)
        self.assertEqual(reader.read_count, 0)
        self.assertEqual(executor.observations, [])

    def test_no_eligible_executor_produces_no_effect(self):
        reader = StaticRepositoryReader((observation(),))
        service, runtime, _telemetry, executor = make_service(reader=reader)

        with self.assertRaisesRegex(
            CoordinatedExecutionError,
            "no_eligible_executor",
        ):
            service.execute(
                request(
                    requirement=execution_requirement(
                        capability="repository.write"
                    )
                )
            )

        self.assertEqual(
            runtime.snapshot().graph.processes[PROCESS_ID].state,
            ProcessState.READY,
        )
        self.assertEqual(reader.read_count, 0)
        self.assertEqual(executor.observations, [])

    def test_generation_change_after_packet_planning_fences_effect(self):
        reader = StaticRepositoryReader((observation(),))
        runtime, clock, telemetry = make_runtime()

        class RecoveringAuthorityEvaluator:
            def evaluate(self, action_candidate):
                runtime.recover(
                    PROCESS_ID,
                    expected_generation=0,
                    reason="injected race after routing and packet compilation",
                )
                return allow_decision(generation=0)

        profile = executor_profile()
        executor = ReadOnlyRepositoryExecutor(reader=reader, clock=clock)
        validator = RepositoryReadPostconditionValidator(
            reader=reader,
            clock=clock,
        )
        service = CoordinatedActionService(
            runtime=runtime,
            registry=ExecutorRegistry((profile,)),
            packet_compiler=SemanticPacketCompiler(),
            authority_evaluator=RecoveringAuthorityEvaluator(),
            executor_ports={profile.executor_id: executor},
            validators={
                RepositoryReadPostconditionValidator.VALIDATOR_ID: validator
            },
        )

        with self.assertRaisesRegex(
            CoordinatedExecutionError,
            "runtime_claim_start_failed:stale_generation",
        ):
            service.execute(request())

        process = runtime.snapshot().graph.processes[PROCESS_ID]
        self.assertEqual(process.generation, 1)
        self.assertEqual(process.state, ProcessState.READY_TO_RESUME)
        self.assertEqual(reader.read_count, 0)
        self.assertEqual(executor.observations, [])
        self.assertIn(
            "process.recovered",
            [record.name for record in telemetry.records],
        )

    def test_changed_source_between_effect_and_validation_returns_repair_ready(self):
        first = observation(content=b"first immutable observation")
        changed = replace(
            observation(content=b"changed observation"),
            blob_id="changed-blob",
        )
        reader = SequencedReader((first, changed))
        service, runtime, _telemetry, executor = make_service(reader=reader)

        result = service.execute(request())

        self.assertFalse(result.completed)
        self.assertFalse(result.validation.passed)
        process = runtime.snapshot().graph.processes[PROCESS_ID]
        self.assertEqual(process.state, ProcessState.READY_TO_RESUME)
        self.assertTrue(process.repair_required)
        self.assertEqual(reader.read_count, 2)
        self.assertEqual(len(executor.observations), 1)
        self.assertEqual(len(process.effect_receipts), 1)

    def test_exact_duplicate_receipt_remains_single_effect(self):
        reader = StaticRepositoryReader((observation(),))
        runtime, clock, _telemetry = make_runtime()
        profile = executor_profile()
        executor = ReadOnlyRepositoryExecutor(reader=reader, clock=clock)

        runtime.claim(
            PROCESS_ID,
            worker_id="W",
            lease_id="L",
            expected_generation=0,
        )
        runtime.start(
            PROCESS_ID,
            lease_id="L",
            expected_generation=0,
        )
        action = DomainKernel.compile_action_spec(
            candidate(),
            allow_decision(),
        )
        receipt = executor.execute(action, executor=profile)

        first = runtime.record_effect(
            PROCESS_ID,
            receipt=receipt,
            lease_id="L",
            expected_generation=0,
        )
        second = runtime.record_effect(
            PROCESS_ID,
            receipt=receipt,
            lease_id="L",
            expected_generation=0,
        )

        self.assertEqual(
            len(first.graph.processes[PROCESS_ID].effect_receipts),
            1,
        )
        self.assertEqual(
            len(second.graph.processes[PROCESS_ID].effect_receipts),
            1,
        )
        self.assertEqual(reader.read_count, 1)


if __name__ == "__main__":
    unittest.main()
