"""Port and deterministic in-memory runtime tests."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    DeterministicFakeExecutor,
    DeterministicSemanticProjection,
    FakeClock,
    InMemoryDurableRuntime,
    InMemoryEventLedger,
    InMemoryStateStore,
    RecordingTelemetry,
    StaticAuthorityEvaluator,
)
from workspace_semantic_execution.application import (  # noqa: E402
    RuntimeCoordinator,
    machine_llm_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    AuthorityDecision,
    AuthorityOutcome,
    CandidateAction,
    DomainKernel,
    ExecutorAvailability,
    ExecutorLifecycle,
    ExecutorLocality,
    KernelError,
    MemoryResetPolicy,
    PrivacyClass,
    ProcessState,
    SessionMode,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    DurableWorkConflict,
    DurableWorkRequest,
    DurableWorkState,
    RuntimeEvent,
    StateConflict,
)


def make_runtime(
    *,
    process_id: str = "R",
):
    store = InMemoryStateStore()
    event_ledger = InMemoryEventLedger()
    clock = FakeClock()
    telemetry = RecordingTelemetry()
    coordinator = RuntimeCoordinator(
        state_store=store,
        event_ledger=event_ledger,
        telemetry=telemetry,
        clock=clock,
    )
    graph = DomainKernel.create_graph(
        [DomainKernel.create_process(process_id)]
    )
    coordinator.initialize(graph)
    return coordinator, store, event_ledger, clock, telemetry


def start_process(
    coordinator: RuntimeCoordinator,
    *,
    process_id: str = "R",
    generation: int = 0,
    worker_id: str = "W",
    lease_id: str = "L",
):
    coordinator.claim(
        process_id,
        worker_id=worker_id,
        lease_id=lease_id,
        expected_generation=generation,
    )
    return coordinator.start(
        process_id,
        lease_id=lease_id,
        expected_generation=generation,
    )


class StateStoreTests(unittest.TestCase):
    def test_stale_compare_and_swap_cannot_overwrite_current_state(self):
        store = InMemoryStateStore()
        graph = DomainKernel.create_graph(
            [DomainKernel.create_process("R")]
        )
        store.initialize(graph)
        first = store.load()
        stale = store.load()

        current_graph = DomainKernel.claim(
            first.graph,
            "R",
            worker_id="W1",
            lease_id="L1",
            expected_generation=0,
        )
        current = store.compare_and_swap(
            expected_version=first.version,
            graph=current_graph,
        )
        self.assertEqual(current.version, 1)

        stale_graph = DomainKernel.claim(
            stale.graph,
            "R",
            worker_id="W2",
            lease_id="L2",
            expected_generation=0,
        )
        with self.assertRaises(StateConflict):
            store.compare_and_swap(
                expected_version=stale.version,
                graph=stale_graph,
            )

        reread = store.load()
        self.assertEqual(reread.version, 1)
        self.assertEqual(reread.graph.processes["R"].worker_id, "W1")

    def test_loaded_graph_is_detached_from_store(self):
        store = InMemoryStateStore()
        graph = DomainKernel.create_graph(
            [DomainKernel.create_process("R")]
        )
        store.initialize(graph)
        detached = store.load()
        detached.graph.processes["R"].generation = 999

        reread = store.load()
        self.assertEqual(reread.graph.processes["R"].generation, 0)


class BoundedDurableRuntimeTests(unittest.TestCase):
    def test_work_id_is_idempotency_key_and_conflicts_fail_closed(self):
        runtime = InMemoryDurableRuntime()
        request = DurableWorkRequest(
            work_id="work:R:3:reason",
            work_kind="reasoning_quantum",
            payload={"process_id": "R", "generation": 3},
            queue_name="reasoning",
        )
        self.assertTrue(runtime.submit(request))
        self.assertFalse(runtime.submit(request))
        self.assertEqual(
            runtime.get_status(work_id=request.work_id).state,
            DurableWorkState.ENQUEUED,
        )

        conflicting = DurableWorkRequest(
            work_id=request.work_id,
            work_kind="reasoning_quantum",
            payload={"process_id": "R", "generation": 4},
            queue_name="reasoning",
        )
        with self.assertRaises(DurableWorkConflict):
            runtime.submit(conflicting)

    def test_bounded_work_status_lifecycle_is_explicit(self):
        runtime = InMemoryDurableRuntime()
        request = DurableWorkRequest(
            work_id="work:A",
            work_kind="effect",
            payload={"action_id": "A"},
        )
        runtime.submit(request)
        running = runtime.mark_running(work_id="work:A")
        self.assertEqual(running.state, DurableWorkState.RUNNING)
        completed = runtime.complete(
            work_id="work:A",
            result_ref="receipt:A",
        )
        self.assertEqual(completed.state, DurableWorkState.COMPLETED)
        self.assertEqual(completed.result_ref, "receipt:A")


class EventDrivenRuntimeTests(unittest.TestCase):
    def test_event_before_wait_is_reconciled_at_wait_boundary(self):
        coordinator, store, _runtime, _clock, telemetry = make_runtime()
        start_process(coordinator)

        version_before_event = store.load().version
        coordinator.publish_external_event(
            RuntimeEvent(
                event_id="E1",
                wait_key="experiment:E1",
                observed_at="T-event",
                payload_ref="artifact:E1",
            )
        )
        self.assertEqual(store.load().version, version_before_event)

        final = coordinator.wait_external(
            "R",
            wait_key="experiment:E1",
            lease_id="L",
            expected_generation=0,
        )
        process = final.graph.processes["R"]
        self.assertEqual(process.state, ProcessState.READY_TO_RESUME)
        self.assertIsNone(process.worker_id)
        self.assertIsNone(process.lease_id)
        self.assertEqual(process.reasoning_quanta, 0)

        names = [record.name for record in telemetry.records]
        self.assertIn("runtime.event_unmatched", names)
        self.assertIn("process.external_wake", names)

    def test_restart_while_waiting_needs_real_event_to_resume(self):
        coordinator1, store, event_ledger, clock, telemetry = make_runtime()
        start_process(coordinator1)
        waiting = coordinator1.wait_external(
            "R",
            wait_key="ci:123",
            lease_id="L",
            expected_generation=0,
        )
        self.assertEqual(
            waiting.graph.processes["R"].state,
            ProcessState.WAITING_EXTERNAL,
        )

        # New coordinator instance: application memory is gone, durable ports remain.
        coordinator2 = RuntimeCoordinator(
            state_store=store,
            event_ledger=event_ledger,
            telemetry=telemetry,
            clock=clock,
        )
        no_event = coordinator2.reconcile_published_events()
        self.assertEqual(
            no_event.graph.processes["R"].state,
            ProcessState.WAITING_EXTERNAL,
        )

        resumed = coordinator2.publish_external_event(
            RuntimeEvent(
                event_id="ci:123:complete",
                wait_key="ci:123",
                observed_at="T-complete",
            )
        )
        self.assertEqual(
            resumed.graph.processes["R"].state,
            ProcessState.READY_TO_RESUME,
        )

    def test_duplicate_external_event_is_idempotent(self):
        coordinator, store, _runtime, _clock, telemetry = make_runtime()
        start_process(coordinator)
        coordinator.wait_external(
            "R",
            wait_key="job:7",
            lease_id="L",
            expected_generation=0,
        )
        event = RuntimeEvent(
            event_id="job:7:done",
            wait_key="job:7",
            observed_at="T-done",
        )
        first = coordinator.publish_external_event(event)
        first_version = first.version
        second = coordinator.publish_external_event(event)

        self.assertEqual(second.version, first_version)
        self.assertEqual(
            second.graph.processes["R"].state,
            ProcessState.READY_TO_RESUME,
        )
        self.assertEqual(
            sum(
                record.name == "runtime.event_duplicate"
                for record in telemetry.records
            ),
            1,
        )

    def test_recovery_during_external_wait_preserves_wait_after_restart(self):
        coordinator1, store, event_ledger, clock, telemetry = make_runtime()
        start_process(coordinator1)
        coordinator1.wait_external(
            "R",
            wait_key="experiment:42",
            lease_id="L",
            expected_generation=0,
        )

        coordinator2 = RuntimeCoordinator(
            state_store=store,
            event_ledger=event_ledger,
            telemetry=telemetry,
            clock=clock,
        )
        recovered = coordinator2.recover(
            "R",
            expected_generation=0,
            reason="service restart",
        )
        process = recovered.graph.processes["R"]
        self.assertEqual(process.generation, 1)
        self.assertEqual(process.state, ProcessState.WAITING_EXTERNAL)
        self.assertEqual(process.wait_key, "experiment:42")

        resumed = coordinator2.publish_external_event(
            RuntimeEvent(
                event_id="experiment:42:done",
                wait_key="experiment:42",
                observed_at="T-done",
            )
        )
        self.assertEqual(
            resumed.graph.processes["R"].state,
            ProcessState.READY_TO_RESUME,
        )
        self.assertEqual(resumed.graph.processes["R"].generation, 1)


class RecoveryAndExecutorLossTests(unittest.TestCase):
    def test_old_executor_cannot_record_effect_after_generation_recovery(self):
        coordinator, _store, _runtime, _clock, _telemetry = make_runtime()
        start_process(coordinator)
        recovered = coordinator.recover(
            "R",
            expected_generation=0,
            reason="executor disappeared",
        )
        self.assertEqual(recovered.graph.processes["R"].generation, 1)

        from workspace_semantic_execution.domain import EffectReceipt

        stale_receipt = EffectReceipt(
            action_id="A",
            idempotency_key="I",
            target_ref="target:A",
            effect_hash="hash:A",
            executor_id="old-executor",
            generation=0,
            observed_at="T-stale",
        )
        with self.assertRaises(KernelError):
            coordinator.record_effect(
                "R",
                receipt=stale_receipt,
                lease_id="L",
                expected_generation=0,
            )

    def test_fake_executor_receipt_generation_comes_from_action_spec(self):
        clock = FakeClock(seconds=5)
        executor = DeterministicFakeExecutor(clock)
        profile = machine_llm_profile(
            executor_id="lab-h100",
            provider_id="lab",
            model_id="model",
            harness_id="h",
            toolset_id="t",
            capabilities=frozenset({"reasoning.bounded"}),
            session_mode=SessionMode.STATELESS,
            lifecycle=ExecutorLifecycle.PERSISTENT_SERVICE,
            memory_reset_policy=MemoryResetPolicy.EVERY_INVOCATION,
            availability=ExecutorAvailability.AVAILABLE,
            locality=ExecutorLocality.INSTITUTIONAL_REMOTE,
            privacy_classes=frozenset({PrivacyClass.PUBLIC}),
            resource_classes=frozenset({"GPU_REMOTE"}),
            context_capacity=32768,
        )
        candidate = CandidateAction(
            action_id="A",
            process_id="R",
            process_generation=3,
            target_ref="target:A",
            executor_type="MACHINE_LLM",
            idempotency_key="I",
            preconditions=(),
            expected_effect="bounded reasoning result",
            postcondition_validator="validator:result",
        )
        decision = AuthorityDecision(
            decision_id="D",
            outcome=AuthorityOutcome.ALLOW,
            action_id="A",
            process_id="R",
            process_generation=3,
            target_ref="target:A",
            authority_scope_ref="scope:A",
        )
        action = DomainKernel.compile_action_spec(candidate, decision)
        receipt = executor.execute(action, executor=profile)

        self.assertEqual(action.process_generation, 3)
        self.assertEqual(receipt.generation, 3)
        self.assertEqual(receipt.action_id, "A")
        self.assertEqual(receipt.executor_id, "lab-h100")


class AuthorityAndProjectionAdapterTests(unittest.TestCase):
    def test_static_authority_defaults_to_unknown_not_allow(self):
        evaluator = StaticAuthorityEvaluator()
        candidate = CandidateAction(
            action_id="A",
            process_id="R",
            process_generation=0,
            target_ref="target:A",
            executor_type="READ_ONLY",
            idempotency_key="I",
            preconditions=(),
            expected_effect="read",
            postcondition_validator="validator:read",
        )
        decision = evaluator.evaluate(candidate)
        self.assertEqual(decision.outcome, AuthorityOutcome.UNKNOWN)
        self.assertEqual(decision.process_generation, 0)
        with self.assertRaises(KernelError):
            DomainKernel.compile_action_spec(candidate, decision)

    def test_semantic_projection_is_deterministic_and_derived(self):
        graph = DomainKernel.create_graph(
            [
                DomainKernel.create_process("B"),
                DomainKernel.create_process("A"),
            ]
        )
        projection = DeterministicSemanticProjection()
        first = projection.project(graph)
        second = projection.project(graph)

        self.assertEqual(first, second)
        self.assertEqual(
            [item["process_id"] for item in first["processes"]],
            ["A", "B"],
        )


if __name__ == "__main__":
    unittest.main()
