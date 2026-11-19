"""Fault-injection acceptance for the semantic-execution backend."""
from __future__ import annotations

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
    RecordingTelemetry,
    dumps_work_graph,
    loads_work_graph,
)
from workspace_semantic_execution.application import RuntimeCoordinator  # noqa: E402
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    EffectReceipt,
    KernelError,
    ProcessState,
    ValidationResult,
)
from workspace_semantic_execution.ports import RuntimeEvent  # noqa: E402


def runtime(process_id: str = "R"):
    store = InMemoryStateStore()
    ledger = InMemoryEventLedger()
    clock = FakeClock()
    telemetry = RecordingTelemetry()
    coordinator = RuntimeCoordinator(
        state_store=store,
        event_ledger=ledger,
        telemetry=telemetry,
        clock=clock,
    )
    coordinator.initialize(
        DomainKernel.create_graph(
            [DomainKernel.create_process(process_id)]
        )
    )
    return coordinator, store, ledger, clock, telemetry


def start(coordinator: RuntimeCoordinator, *, generation: int = 0):
    coordinator.claim(
        "R",
        worker_id=f"W{generation}",
        lease_id=f"L{generation}",
        expected_generation=generation,
    )
    return coordinator.start(
        "R",
        lease_id=f"L{generation}",
        expected_generation=generation,
    )


def receipt(*, generation: int, effect_hash: str = "effect:A") -> EffectReceipt:
    return EffectReceipt(
        action_id="A",
        idempotency_key="idem:A",
        target_ref="target:A",
        effect_hash=effect_hash,
        executor_id="executor:test",
        generation=generation,
        observed_at=f"T:{generation}",
    )


class ClaimAndGenerationFaultTests(unittest.TestCase):
    def test_death_after_claim_fences_old_lease(self):
        coordinator, _store, _ledger, _clock, _telemetry = runtime()
        coordinator.claim(
            "R",
            worker_id="W0",
            lease_id="L0",
            expected_generation=0,
        )

        recovered = coordinator.recover(
            "R",
            expected_generation=0,
            reason="worker died after claim",
        )
        process = recovered.graph.processes["R"]
        self.assertEqual(process.generation, 1)
        self.assertEqual(process.state, ProcessState.READY_TO_RESUME)
        self.assertIsNone(process.worker_id)
        self.assertIsNone(process.lease_id)

        with self.assertRaises(KernelError):
            coordinator.start(
                "R",
                lease_id="L0",
                expected_generation=0,
            )

    def test_executor_loss_rejects_stale_effect(self):
        coordinator, _store, _ledger, _clock, _telemetry = runtime()
        start(coordinator)
        coordinator.recover(
            "R",
            expected_generation=0,
            reason="executor/session disappeared",
        )

        with self.assertRaises(KernelError):
            coordinator.record_effect(
                "R",
                receipt=receipt(generation=0),
                lease_id="L0",
                expected_generation=0,
            )


class EffectCrashFaultTests(unittest.TestCase):
    def test_death_after_effect_before_checkpoint_preserves_exactly_once_receipt(self):
        coordinator, store, ledger, clock, telemetry = runtime()
        start(coordinator)
        coordinator.record_effect(
            "R",
            receipt=receipt(generation=0),
            lease_id="L0",
            expected_generation=0,
        )

        persisted = dumps_work_graph(store.load().graph)
        reloaded = loads_work_graph(persisted)
        replacement_store = InMemoryStateStore()
        replacement_store.initialize(reloaded)
        replacement = RuntimeCoordinator(
            state_store=replacement_store,
            event_ledger=ledger,
            telemetry=telemetry,
            clock=clock,
        )
        recovered = replacement.recover(
            "R",
            expected_generation=0,
            reason="process died after external effect",
        )
        self.assertEqual(
            len(recovered.graph.processes["R"].effect_receipts),
            1,
        )

        replacement.claim(
            "R",
            worker_id="W1",
            lease_id="L1",
            expected_generation=1,
        )
        replacement.start(
            "R",
            lease_id="L1",
            expected_generation=1,
        )
        replacement.propose_terminal(
            "R",
            lease_id="L1",
            expected_generation=1,
        )
        replacement.begin_validation("R")
        final = replacement.record_validation(
            "R",
            result=ValidationResult(
                validator_id="validator:A",
                passed=True,
                evidence_ref="evidence:A",
                observed_at="T:validated",
            ),
        )
        self.assertEqual(
            final.graph.processes["R"].state,
            ProcessState.COMPLETED,
        )
        self.assertEqual(
            len(final.graph.processes["R"].effect_receipts),
            1,
        )

    def test_conflicting_duplicate_effect_after_restart_fails_closed(self):
        coordinator, store, ledger, clock, telemetry = runtime()
        start(coordinator)
        coordinator.record_effect(
            "R",
            receipt=receipt(generation=0, effect_hash="original"),
            lease_id="L0",
            expected_generation=0,
        )
        coordinator.recover(
            "R",
            expected_generation=0,
            reason="restart",
        )
        coordinator.claim(
            "R",
            worker_id="W1",
            lease_id="L1",
            expected_generation=1,
        )
        coordinator.start(
            "R",
            lease_id="L1",
            expected_generation=1,
        )

        with self.assertRaises(KernelError):
            coordinator.record_effect(
                "R",
                receipt=receipt(generation=1, effect_hash="conflict"),
                lease_id="L1",
                expected_generation=1,
            )


class EventOrderingFaultTests(unittest.TestCase):
    def test_out_of_order_event_before_wait_is_reconciled_without_polling(self):
        coordinator, _store, _ledger, _clock, telemetry = runtime()
        coordinator.publish_external_event(
            RuntimeEvent(
                event_id="experiment:1:done",
                wait_key="experiment:1",
                observed_at="T:event",
            )
        )
        start(coordinator)
        final = coordinator.wait_external(
            "R",
            wait_key="experiment:1",
            lease_id="L0",
            expected_generation=0,
        )
        self.assertEqual(
            final.graph.processes["R"].state,
            ProcessState.READY_TO_RESUME,
        )
        names = [record.name for record in telemetry.records]
        self.assertIn("runtime.event_unmatched", names)
        self.assertIn("process.external_wake", names)

    def test_delayed_wrong_event_does_not_wake_unrelated_wait(self):
        coordinator, store, _ledger, _clock, _telemetry = runtime()
        start(coordinator)
        coordinator.wait_external(
            "R",
            wait_key="ci:right",
            lease_id="L0",
            expected_generation=0,
        )
        before = store.load().version
        wrong = coordinator.publish_external_event(
            RuntimeEvent(
                event_id="ci:wrong:done",
                wait_key="ci:wrong",
                observed_at="T:wrong",
            )
        )
        self.assertEqual(wrong.version, before)
        self.assertEqual(
            wrong.graph.processes["R"].state,
            ProcessState.WAITING_EXTERNAL,
        )

    def test_duplicate_event_does_not_replay_wake(self):
        coordinator, _store, _ledger, _clock, telemetry = runtime()
        start(coordinator)
        coordinator.wait_external(
            "R",
            wait_key="ci:dup",
            lease_id="L0",
            expected_generation=0,
        )
        event = RuntimeEvent(
            event_id="ci:dup:done",
            wait_key="ci:dup",
            observed_at="T:done",
        )
        first = coordinator.publish_external_event(event)
        second = coordinator.publish_external_event(event)
        self.assertEqual(first.version, second.version)
        self.assertEqual(
            sum(
                record.name == "runtime.event_duplicate"
                for record in telemetry.records
            ),
            1,
        )


class ValidatorFaultTests(unittest.TestCase):
    def test_validator_timeout_never_completes_and_can_resume_repair(self):
        coordinator, _store, _ledger, _clock, _telemetry = runtime()
        start(coordinator)
        coordinator.record_effect(
            "R",
            receipt=receipt(generation=0),
            lease_id="L0",
            expected_generation=0,
        )
        coordinator.propose_terminal(
            "R",
            lease_id="L0",
            expected_generation=0,
        )
        validating = coordinator.begin_validation("R")
        self.assertEqual(
            validating.graph.processes["R"].state,
            ProcessState.VALIDATING,
        )

        recovered = coordinator.recover(
            "R",
            expected_generation=0,
            reason="validator timeout",
        )
        process = recovered.graph.processes["R"]
        self.assertEqual(process.generation, 1)
        self.assertEqual(process.state, ProcessState.READY_TO_RESUME)
        self.assertEqual(len(process.effect_receipts), 1)

        with self.assertRaises(KernelError):
            coordinator.record_validation(
                "R",
                result=ValidationResult(
                    validator_id="late-validator",
                    passed=True,
                    evidence_ref="late:evidence",
                    observed_at="T:late",
                ),
            )

        coordinator.claim(
            "R",
            worker_id="W1",
            lease_id="L1",
            expected_generation=1,
        )
        coordinator.start(
            "R",
            lease_id="L1",
            expected_generation=1,
        )
        coordinator.propose_terminal(
            "R",
            lease_id="L1",
            expected_generation=1,
        )
        coordinator.begin_validation("R")
        final = coordinator.record_validation(
            "R",
            result=ValidationResult(
                validator_id="validator:retry",
                passed=True,
                evidence_ref="evidence:retry",
                observed_at="T:retry",
            ),
        )
        self.assertEqual(
            final.graph.processes["R"].state,
            ProcessState.COMPLETED,
        )


class WaitRecoveryFaultTests(unittest.TestCase):
    def test_restart_during_external_wait_preserves_wait_until_real_event(self):
        coordinator, store, ledger, clock, telemetry = runtime()
        start(coordinator)
        coordinator.wait_external(
            "R",
            wait_key="experiment:pending",
            lease_id="L0",
            expected_generation=0,
        )
        persisted = dumps_work_graph(store.load().graph)
        replacement_store = InMemoryStateStore()
        replacement_store.initialize(loads_work_graph(persisted))
        replacement = RuntimeCoordinator(
            state_store=replacement_store,
            event_ledger=ledger,
            telemetry=telemetry,
            clock=clock,
        )
        recovered = replacement.recover(
            "R",
            expected_generation=0,
            reason="backend restart",
        )
        self.assertEqual(
            recovered.graph.processes["R"].state,
            ProcessState.WAITING_EXTERNAL,
        )
        self.assertEqual(
            recovered.graph.processes["R"].wait_key,
            "experiment:pending",
        )

        final = replacement.publish_external_event(
            RuntimeEvent(
                event_id="experiment:pending:done",
                wait_key="experiment:pending",
                observed_at="T:done",
            )
        )
        self.assertEqual(
            final.graph.processes["R"].state,
            ProcessState.READY_TO_RESUME,
        )
        self.assertEqual(final.graph.processes["R"].generation, 1)


if __name__ == "__main__":
    unittest.main()
