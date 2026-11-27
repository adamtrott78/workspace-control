"""Production scheduler + immutable GitHub candidate transport tests."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    DeterministicFakeExecutor,
    FakeClock,
    GitHubCandidateEventService,
    GitHubCandidateObservation,
    InMemoryEventLedger,
    InMemoryStateStore,
    RecordingTelemetry,
    StaticAuthorityEvaluator,
    dumps_work_graph,
    loads_work_graph,
)
from workspace_semantic_execution.application import (  # noqa: E402
    ExecutorDispatchCoordinator,
    ExecutorRegistry,
    PersistentExecutorSessionBroker,
    ProductionSchedulerService,
    RuntimeCoordinator,
    SemanticPacketCompiler,
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
    SchedulerDeterministicSpec,
    SchedulerDispatchSpec,
    SchedulerOperatorSpec,
    SchedulerPacketSpec,
    SessionMode,
    ValidationResult,
)


DET_ID = "det-ready"
INSTANT_ID = "instant-ready"
WAIT_ID = "wait-external"
UNPLANNED_ID = "unplanned-ready"
SLOT_ID = "instant-production-slot"
VALIDATOR_ID = "validator:production-scheduler"
CANDIDATE_REPO = "adamtrott78/workspace-control"
CANDIDATE_REF = "refs/heads/worker-result-candidates-v1"
CANDIDATE_PATH = "worker-results/candidates/instant-production.json"
INSTANT = openai_chat_instant_current_profile()


def deterministic_profile() -> ExecutorProfile:
    return ExecutorProfile(
        executor_id="deterministic-production-test",
        provider_id="workspace-control",
        model_id="none",
        surface_id="machine",
        harness_id="deterministic-fake-v1",
        toolset_id="deterministic-fake",
        capabilities=frozenset({"deterministic.test"}),
        invocation_mode=InvocationMode.DETERMINISTIC,
        session_mode=SessionMode.NONE,
        lifecycle=ExecutorLifecycle.DETERMINISTIC_PROCESS,
        memory_reset_policy=MemoryResetPolicy.NONE,
        availability=ExecutorAvailability.AVAILABLE,
        locality=ExecutorLocality.LOCAL_HOST,
        privacy_classes=frozenset({PrivacyClass.INTERNAL}),
        resource_classes=frozenset({"CPU"}),
        scarcity_rank=0,
    )


def deterministic_requirement() -> ExecutionRequirement:
    return ExecutionRequirement(
        required_capabilities=frozenset({"deterministic.test"}),
        allowed_invocation_modes=frozenset(
            {InvocationMode.DETERMINISTIC}
        ),
        allowed_session_modes=frozenset({SessionMode.NONE}),
        privacy_class=PrivacyClass.INTERNAL,
        required_resource_classes=frozenset({"CPU"}),
        require_human_launch=False,
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


class PassingPostconditionValidator:
    def validate(self, action, receipt):
        return ValidationResult(
            validator_id="validator:deterministic-test",
            passed=True,
            evidence_ref=f"validated:{receipt.effect_hash}",
            observed_at="T-validator",
        )


class PassingWorkerValidator:
    def __init__(self):
        self.calls = 0

    def validate(self, publication, packet_source):
        self.calls += 1
        return ValidationResult(
            validator_id=VALIDATOR_ID,
            passed=True,
            evidence_ref=(
                "validated-worker:"
                f"{publication.source_sha256}"
            ),
            observed_at="T-worker-validator",
        )


class StaticCandidateReader:
    def __init__(self, observation):
        self.observation = observation
        self.calls = 0

    def read_exact(
        self,
        *,
        repository,
        ref,
        path,
        commit_sha,
    ):
        self.calls += 1
        return self.observation


def build_runtime() -> RuntimeCoordinator:
    graph = DomainKernel.create_graph(
        [
            DomainKernel.create_process(DET_ID),
            DomainKernel.create_process(INSTANT_ID),
            DomainKernel.create_process(WAIT_ID),
            DomainKernel.create_process(UNPLANNED_ID),
        ]
    )
    graph = DomainKernel.claim(
        graph,
        WAIT_ID,
        worker_id="wait-worker",
        lease_id="wait-lease",
        expected_generation=0,
    )
    graph = DomainKernel.start(
        graph,
        WAIT_ID,
        lease_id="wait-lease",
        expected_generation=0,
    )
    graph = DomainKernel.wait_external(
        graph,
        WAIT_ID,
        wait_key="external:artifact:123",
        lease_id="wait-lease",
        expected_generation=0,
    )

    runtime = RuntimeCoordinator(
        state_store=InMemoryStateStore(),
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    runtime.initialize(graph)
    PersistentExecutorSessionBroker(runtime).ensure_session(
        profile=INSTANT,
        slot_id=SLOT_ID,
        session_id="chat-production-scheduler",
    )
    return runtime


def deterministic_spec() -> SchedulerDispatchSpec:
    action = CandidateAction(
        action_id="effect:det-ready",
        process_id=DET_ID,
        process_generation=0,
        target_ref="fake://deterministic/target",
        executor_type="DETERMINISTIC_TEST",
        idempotency_key="det-ready:v1",
        preconditions=("bounded-test-target",),
        expected_effect="produce deterministic receipt",
        postcondition_validator="validator:deterministic-test",
    )
    return SchedulerDispatchSpec(
        dispatch_id="01-deterministic",
        process_id=DET_ID,
        process_generation=0,
        requirement_id="requirement:det-ready",
        requirement=deterministic_requirement(),
        packet=SchedulerPacketSpec(
            source_checkpoint="scheduler@det-ready",
            objective="Execute the bounded deterministic action.",
            constraints=("no unreviewed authority",),
            evidence_refs=("evidence:det-ready",),
            authority_refs=("scope:det-test",),
            allowed_actions=("execute-bounded-test",),
            validator_contract="validator:deterministic-test",
            output_schema="schema:deterministic-test",
            next_safe_boundary="return validated effect receipt",
        ),
        deterministic=SchedulerDeterministicSpec(
            worker_id="det-worker",
            lease_id="det-lease",
            candidate_action=action,
        ),
    )


def instant_spec(
    *,
    dispatch_id: str = "02-instant",
    process_generation: int = 0,
    session_generation: int = 0,
    action_id: str = "action:instant-production",
    candidate_path: str = CANDIDATE_PATH,
    queue_sequence: int = 1,
) -> SchedulerDispatchSpec:
    return SchedulerDispatchSpec(
        dispatch_id=dispatch_id,
        process_id=INSTANT_ID,
        process_generation=process_generation,
        requirement_id=(
            "requirement:instant-ready:"
            f"g{process_generation}"
        ),
        requirement=instant_requirement(),
        packet=SchedulerPacketSpec(
            source_checkpoint=(
                "scheduler@instant-ready:"
                f"g{process_generation}"
            ),
            objective="Return one immutable candidate result.",
            constraints=(
                "candidate-only publication",
                "no authority mutation",
            ),
            evidence_refs=("evidence:instant-ready",),
            authority_refs=("scope:proposal-only",),
            allowed_actions=("publish-candidate-result",),
            validator_contract=VALIDATOR_ID,
            output_schema="WORKER_RESULT_V1",
            next_safe_boundary="publish immutable candidate JSON",
        ),
        operator=SchedulerOperatorSpec(
            task_id="scheduler-production-test",
            action_id=action_id,
            action_generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=session_generation,
            priority_rank=10,
            queue_sequence=queue_sequence,
            created_at=f"T{queue_sequence}",
            candidate_repository=CANDIDATE_REPO,
            candidate_ref=CANDIDATE_REF,
            candidate_path=candidate_path,
        ),
    )


def build_scheduler(runtime):
    deterministic = deterministic_profile()
    candidate = deterministic_spec().deterministic.candidate_action
    authority = AuthorityDecision(
        decision_id="allow:det-ready",
        outcome=AuthorityOutcome.ALLOW,
        action_id=candidate.action_id,
        process_id=candidate.process_id,
        process_generation=candidate.process_generation,
        target_ref=candidate.target_ref,
        authority_scope_ref="scope:det-test",
    )
    dispatcher = ExecutorDispatchCoordinator(
        runtime=runtime,
        registry=ExecutorRegistry((deterministic, INSTANT)),
        packet_compiler=SemanticPacketCompiler(),
        authority_evaluator=StaticAuthorityEvaluator(
            {candidate.action_id: authority}
        ),
        executor_ports={
            deterministic.executor_id: DeterministicFakeExecutor(
                FakeClock(seconds=20)
            )
        },
        validators={
            "validator:deterministic-test":
                PassingPostconditionValidator()
        },
    )
    return ProductionSchedulerService(
        runtime=runtime,
        dispatcher=dispatcher,
    )


def worker_candidate_bytes(
    runtime,
    *,
    action_id: str = "action:instant-production",
) -> bytes:
    graph = runtime.snapshot().graph
    action = graph.operator_actions[action_id]
    source = graph.packet_sources[action.payload_ref]
    contract = source.result_publication
    assert contract is not None
    return json.dumps(
        {
            "publication_id": contract.publication_id,
            "action_id": action.action_id,
            "action_generation": action.generation,
            "process_id": INSTANT_ID,
            "process_generation": action.process_generation,
            "executor_id": INSTANT.executor_id,
            "worker_slot_id": SLOT_ID,
            "session_generation": action.session_generation,
            "packet_sha256": action.payload_sha256,
            "kind": "RESULT",
            "observed_at": "T-result",
            "result_payload_ref": (
                "github://scheduler-result-payload@immutable"
            ),
            "result_payload_sha256": "e" * 64,
            "evidence_refs": ["evidence:scheduler-worker"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class ProductionSchedulerTests(unittest.TestCase):
    def test_ready_only_dispatch_wait_zero_mutation_and_candidate_event_completion(self):
        runtime = build_runtime()
        scheduler = build_scheduler(runtime)
        scheduler.register(deterministic_spec())
        scheduler.register(instant_spec())

        serialized = dumps_work_graph(runtime.snapshot().graph)
        restored = loads_work_graph(serialized)
        self.assertEqual(
            restored.scheduler_dispatches,
            runtime.snapshot().graph.scheduler_dispatches,
        )

        first = scheduler.run_once()
        self.assertEqual(first.outcome, "DISPATCHED")
        self.assertEqual(first.dispatch_id, "01-deterministic")
        self.assertEqual(
            first.dispatch_mode,
            "DETERMINISTIC_EFFECT",
        )
        self.assertEqual(
            runtime.snapshot().graph.processes[DET_ID].state,
            ProcessState.COMPLETED,
        )
        self.assertEqual(
            runtime.snapshot().graph.processes[WAIT_ID].state,
            ProcessState.WAITING_EXTERNAL,
        )

        second = scheduler.run_once()
        self.assertEqual(second.outcome, "DISPATCHED")
        self.assertEqual(second.dispatch_id, "02-instant")
        self.assertEqual(second.dispatch_mode, "OPERATOR_ACTION")
        self.assertEqual(
            runtime.snapshot().graph.processes[INSTANT_ID].state,
            ProcessState.RUNNING,
        )
        self.assertEqual(
            runtime.snapshot().graph.operator_actions[
                "action:instant-production"
            ].status,
            OperatorActionState.QUEUED,
        )

        version_before_idle = runtime.snapshot().version
        wait_quanta = runtime.snapshot().graph.processes[
            WAIT_ID
        ].reasoning_quanta
        idle = scheduler.run_once()
        self.assertEqual(idle.outcome, "UNPLANNED_READY")
        self.assertEqual(
            idle.unplanned_ready_processes,
            (UNPLANNED_ID,),
        )
        self.assertEqual(runtime.snapshot().version, version_before_idle)
        self.assertEqual(
            runtime.snapshot().graph.processes[
                WAIT_ID
            ].reasoning_quanta,
            wait_quanta,
        )
        self.assertEqual(
            runtime.snapshot().graph.processes[WAIT_ID].wait_key,
            "external:artifact:123",
        )

        runtime.claim_next_operator_action(
            helper_instance_id="windows-helper",
            claim_id="claim:instant-production",
            claimed_at="T1",
            expires_at="T2",
        )
        runtime.record_operator_action_local_prepared(
            action_id="action:instant-production",
            generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            observed_at="T1.5",
        )

        raw = worker_candidate_bytes(runtime)
        commit = "a" * 40
        observation = GitHubCandidateObservation(
            repository=CANDIDATE_REPO,
            ref=CANDIDATE_REF,
            path=CANDIDATE_PATH,
            commit_sha=commit,
            content=raw,
        )
        reader = StaticCandidateReader(observation)
        validator = PassingWorkerValidator()
        event_service = GitHubCandidateEventService(
            runtime=runtime,
            intake=WorkerResultIntakeService(
                runtime=runtime,
                validators={VALIDATOR_ID: validator},
            ),
            reader=reader,
        )
        outcome = event_service.ingest(
            dispatch_id="02-instant",
            commit_sha=commit,
        )
        self.assertEqual(outcome.process_state, ProcessState.COMPLETED)
        self.assertEqual(validator.calls, 1)
        self.assertEqual(
            runtime.snapshot().graph.operator_actions[
                "action:instant-production"
            ].status,
            OperatorActionState.COMPLETED,
        )

        duplicate = event_service.ingest(
            dispatch_id="02-instant",
            commit_sha=commit,
        )
        self.assertEqual(
            duplicate.process_state,
            ProcessState.COMPLETED,
        )
        self.assertEqual(validator.calls, 1)
        self.assertEqual(
            len(runtime.snapshot().graph.worker_results),
            1,
        )

    def test_recovery_requires_new_generation_plan_and_replacement_session(self):
        runtime = build_runtime()
        scheduler = build_scheduler(runtime)
        first_spec = instant_spec()
        scheduler.register(first_spec)

        first_tick = scheduler.run_once()
        self.assertEqual(first_tick.outcome, "DISPATCHED")
        runtime.claim_next_operator_action(
            helper_instance_id="windows-helper",
            claim_id="claim:g0",
            claimed_at="T1",
            expires_at="T2",
        )
        runtime.record_operator_action_local_prepared(
            action_id="action:instant-production",
            generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            observed_at="T1.5",
        )
        old_bytes = worker_candidate_bytes(runtime)
        old_observation = GitHubCandidateObservation(
            repository=CANDIDATE_REPO,
            ref=CANDIDATE_REF,
            path=CANDIDATE_PATH,
            commit_sha="c" * 40,
            content=old_bytes,
        )

        runtime.recover(
            INSTANT_ID,
            expected_generation=0,
            reason="scheduler_worker_session_lost",
        )
        graph = runtime.snapshot().graph
        self.assertEqual(
            graph.processes[INSTANT_ID].generation,
            1,
        )
        self.assertEqual(
            graph.processes[INSTANT_ID].state,
            ProcessState.READY_TO_RESUME,
        )
        self.assertEqual(
            graph.operator_actions[
                "action:instant-production"
            ].status,
            OperatorActionState.STALE,
        )
        self.assertEqual(
            graph.executor_sessions[SLOT_ID].state.value,
            "NEEDS_REPLACEMENT",
        )

        version_before_tick = runtime.snapshot().version
        stale_tick = scheduler.run_once()
        self.assertEqual(stale_tick.outcome, "UNPLANNED_READY")
        self.assertIn(
            INSTANT_ID,
            stale_tick.unplanned_ready_processes,
        )
        self.assertEqual(
            runtime.snapshot().version,
            version_before_tick,
            "old generation scheduler plan must not redispatch",
        )

        late_service = GitHubCandidateEventService(
            runtime=runtime,
            intake=WorkerResultIntakeService(
                runtime=runtime,
                validators={
                    VALIDATOR_ID: PassingWorkerValidator()
                },
            ),
            reader=StaticCandidateReader(old_observation),
        )
        version_before_late = runtime.snapshot().version
        with self.assertRaisesRegex(
            RuntimeError,
            "worker_result_action_not_awaiting_ack|"
            "worker_result_process_binding_mismatch",
        ):
            late_service.ingest(
                dispatch_id=first_spec.dispatch_id,
                commit_sha="c" * 40,
            )
        self.assertEqual(
            runtime.snapshot().version,
            version_before_late,
        )

        PersistentExecutorSessionBroker(runtime).replace(
            slot_id=SLOT_ID,
            expected_session_generation=1,
            session_id="chat-production-scheduler-replacement",
        )
        replacement_path = (
            "worker-results/candidates/"
            "instant-production-g1.json"
        )
        replacement_spec = instant_spec(
            dispatch_id="03-instant-g1",
            process_generation=1,
            session_generation=1,
            action_id="action:instant-production:g1",
            candidate_path=replacement_path,
            queue_sequence=2,
        )
        scheduler.register(replacement_spec)
        replacement_tick = scheduler.run_once()
        self.assertEqual(
            replacement_tick.outcome,
            "DISPATCHED",
        )
        self.assertEqual(
            replacement_tick.dispatch_id,
            replacement_spec.dispatch_id,
        )
        runtime.claim_next_operator_action(
            helper_instance_id="windows-helper",
            claim_id="claim:g1",
            claimed_at="T3",
            expires_at="T4",
        )
        runtime.record_operator_action_local_prepared(
            action_id="action:instant-production:g1",
            generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=1,
            observed_at="T3.5",
        )
        replacement_bytes = worker_candidate_bytes(
            runtime,
            action_id="action:instant-production:g1",
        )
        replacement_observation = GitHubCandidateObservation(
            repository=CANDIDATE_REPO,
            ref=CANDIDATE_REF,
            path=replacement_path,
            commit_sha="d" * 40,
            content=replacement_bytes,
        )
        validator = PassingWorkerValidator()
        outcome = GitHubCandidateEventService(
            runtime=runtime,
            intake=WorkerResultIntakeService(
                runtime=runtime,
                validators={VALIDATOR_ID: validator},
            ),
            reader=StaticCandidateReader(
                replacement_observation
            ),
        ).ingest(
            dispatch_id=replacement_spec.dispatch_id,
            commit_sha="d" * 40,
        )
        self.assertEqual(
            outcome.process_state,
            ProcessState.COMPLETED,
        )
        final = runtime.snapshot().graph
        self.assertEqual(
            final.operator_actions[
                "action:instant-production"
            ].status,
            OperatorActionState.STALE,
        )
        self.assertEqual(
            final.operator_actions[
                "action:instant-production:g1"
            ].status,
            OperatorActionState.COMPLETED,
        )
        self.assertEqual(
            final.executor_sessions[SLOT_ID].state.value,
            "READY",
        )
        self.assertEqual(
            final.executor_sessions[SLOT_ID].session_generation,
            1,
        )

    def test_wait_only_scheduler_soak_is_non_mutating_and_zero_reasoning(self):
        graph = DomainKernel.create_graph(
            [DomainKernel.create_process("wait-soak")]
        )
        graph = DomainKernel.claim(
            graph,
            "wait-soak",
            worker_id="wait-soak-worker",
            lease_id="wait-soak-lease",
            expected_generation=0,
        )
        graph = DomainKernel.start(
            graph,
            "wait-soak",
            lease_id="wait-soak-lease",
            expected_generation=0,
        )
        graph = DomainKernel.wait_external(
            graph,
            "wait-soak",
            wait_key="external:soak",
            lease_id="wait-soak-lease",
            expected_generation=0,
        )
        runtime = RuntimeCoordinator(
            state_store=InMemoryStateStore(),
            event_ledger=InMemoryEventLedger(),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        runtime.initialize(graph)
        scheduler = build_scheduler(runtime)
        before = runtime.snapshot()
        for _ in range(1000):
            tick = scheduler.run_once()
            self.assertEqual(tick.outcome, "NO_WORK")
        after = runtime.snapshot()
        self.assertEqual(after.version, before.version)
        self.assertEqual(
            after.graph.processes["wait-soak"].reasoning_quanta,
            0,
        )
        self.assertEqual(
            after.graph.processes["wait-soak"].wait_key,
            "external:soak",
        )

    def test_candidate_observation_mismatch_is_pre_mutation_failure(self):
        runtime = build_runtime()
        scheduler = build_scheduler(runtime)
        scheduler.register(instant_spec())
        scheduler.run_once()
        runtime.claim_next_operator_action(
            helper_instance_id="windows-helper",
            claim_id="claim",
            claimed_at="T1",
            expires_at="T2",
        )
        runtime.record_operator_action_local_prepared(
            action_id="action:instant-production",
            generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            observed_at="T1.5",
        )
        raw = worker_candidate_bytes(runtime)
        bad = GitHubCandidateObservation(
            repository=CANDIDATE_REPO,
            ref=CANDIDATE_REF,
            path="worker-results/candidates/wrong.json",
            commit_sha="b" * 40,
            content=raw,
        )
        service = GitHubCandidateEventService(
            runtime=runtime,
            intake=WorkerResultIntakeService(
                runtime=runtime,
                validators={
                    VALIDATOR_ID: PassingWorkerValidator()
                },
            ),
            reader=StaticCandidateReader(bad),
        )
        version = runtime.snapshot().version
        with self.assertRaisesRegex(
            RuntimeError,
            "candidate_observation_binding_mismatch",
        ):
            service.ingest(
                dispatch_id="02-instant",
                commit_sha="b" * 40,
            )
        self.assertEqual(runtime.snapshot().version, version)
        self.assertEqual(runtime.snapshot().graph.worker_results, {})

    def test_candidate_namespace_and_duplicate_process_generation_plan_fail_closed(self):
        runtime = build_runtime()
        scheduler = build_scheduler(runtime)
        scheduler.register(instant_spec())

        conflicting = instant_spec()
        conflicting = SchedulerDispatchSpec(
            dispatch_id="different-id",
            process_id=conflicting.process_id,
            process_generation=conflicting.process_generation,
            requirement_id=conflicting.requirement_id,
            requirement=conflicting.requirement,
            packet=conflicting.packet,
            operator=conflicting.operator,
        )
        with self.assertRaisesRegex(
            RuntimeError,
            "scheduler_dispatch_process_generation_conflict",
        ):
            scheduler.register(conflicting)

        bad_operator = SchedulerOperatorSpec(
            task_id="bad",
            action_id="bad-action",
            action_generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            priority_rank=1,
            queue_sequence=1,
            created_at="T0",
            candidate_repository=CANDIDATE_REPO,
            candidate_ref="refs/heads/main",
            candidate_path="tasks/active/forbidden.json",
        )
        bad_spec = SchedulerDispatchSpec(
            dispatch_id="bad-spec",
            process_id=UNPLANNED_ID,
            process_generation=0,
            requirement_id="bad-requirement",
            requirement=instant_requirement(),
            packet=SchedulerPacketSpec(
                source_checkpoint="bad",
                objective="bad",
                validator_contract=VALIDATOR_ID,
                output_schema="WORKER_RESULT_V1",
                next_safe_boundary="bad",
            ),
            operator=bad_operator,
        )
        with self.assertRaisesRegex(
            RuntimeError,
            "scheduler_dispatch_candidate_ref_invalid",
        ):
            scheduler.register(bad_spec)


if __name__ == "__main__":
    unittest.main()
