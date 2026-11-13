"""Dedicated DBOS + PostgreSQL integration spike.

Ordinary repository validation skips this module unless
SEMANTIC_EXECUTION_INTEGRATION=1. The dedicated semantic-execution workflow
installs pinned DBOS/PostgreSQL dependencies and supplies a disposable database.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
import sys
import time
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    DBOSDurableRuntime,
    FakeClock,
    PostgresEventLedger,
    PostgresStateStore,
    RecordingTelemetry,
)
from workspace_semantic_execution.application import RuntimeCoordinator  # noqa: E402
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    ProcessState,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    DurableWorkConflict,
    DurableWorkRequest,
    DurableWorkState,
    RuntimeEvent,
    StateConflict,
)


RUN_INTEGRATION = os.environ.get("SEMANTIC_EXECUTION_INTEGRATION") == "1"
POSTGRES_DSN = os.environ.get("SEMANTIC_EXECUTION_POSTGRES_DSN", "")
DBOS_DSN = os.environ.get("DBOS_SYSTEM_DATABASE_URL", "")


@unittest.skipUnless(
    RUN_INTEGRATION and POSTGRES_DSN,
    "dedicated semantic-execution PostgreSQL integration only",
)
class PostgresAdapterIntegrationTests(unittest.TestCase):
    def test_state_store_cas_survives_adapter_reinstantiation(self):
        state_key = f"state-{uuid.uuid4()}"
        first_store = PostgresStateStore(
            POSTGRES_DSN,
            state_key=state_key,
        )
        graph = DomainKernel.create_graph(
            [DomainKernel.create_process("R")]
        )
        initialized = first_store.initialize(graph)
        self.assertEqual(initialized.version, 0)

        stale = first_store.load()
        claimed = DomainKernel.claim(
            stale.graph,
            "R",
            worker_id="W1",
            lease_id="L1",
            expected_generation=0,
        )
        current = first_store.compare_and_swap(
            expected_version=stale.version,
            graph=claimed,
        )
        self.assertEqual(current.version, 1)

        restarted_store = PostgresStateStore(
            POSTGRES_DSN,
            state_key=state_key,
        )
        reread = restarted_store.load()
        self.assertEqual(reread.version, 1)
        self.assertEqual(reread.graph.processes["R"].worker_id, "W1")

        with self.assertRaises(StateConflict):
            restarted_store.compare_and_swap(
                expected_version=stale.version,
                graph=stale.graph,
            )

    def test_external_event_is_immutable_and_visible_after_restart(self):
        ledger1 = PostgresEventLedger(POSTGRES_DSN)
        event_id = f"event-{uuid.uuid4()}"
        wait_key = f"wait-{uuid.uuid4()}"
        event = RuntimeEvent(
            event_id=event_id,
            wait_key=wait_key,
            observed_at="T1",
            payload_ref="artifact:1",
        )
        self.assertTrue(ledger1.publish_event(event))
        self.assertFalse(ledger1.publish_event(event))

        ledger2 = PostgresEventLedger(POSTGRES_DSN)
        self.assertEqual(
            ledger2.find_event(wait_key=wait_key),
            event,
        )

        with self.assertRaises(ValueError):
            ledger2.publish_event(
                RuntimeEvent(
                    event_id=event_id,
                    wait_key=wait_key,
                    observed_at="DIFFERENT",
                    payload_ref="artifact:1",
                )
            )

    def test_semantic_wait_resumes_after_process_restart_without_polling(self):
        state_key = f"restart-{uuid.uuid4()}"
        wait_key = f"experiment-{uuid.uuid4()}"
        event_id = f"event-{uuid.uuid4()}"

        store1 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        ledger1 = PostgresEventLedger(POSTGRES_DSN)
        telemetry1 = RecordingTelemetry()
        coordinator1 = RuntimeCoordinator(
            state_store=store1,
            event_ledger=ledger1,
            telemetry=telemetry1,
            clock=FakeClock(),
        )
        coordinator1.initialize(
            DomainKernel.create_graph(
                [DomainKernel.create_process("R")]
            )
        )
        coordinator1.claim(
            "R",
            worker_id="W",
            lease_id="L",
            expected_generation=0,
        )
        coordinator1.start(
            "R",
            lease_id="L",
            expected_generation=0,
        )
        waiting = coordinator1.wait_external(
            "R",
            wait_key=wait_key,
            lease_id="L",
            expected_generation=0,
        )
        self.assertEqual(
            waiting.graph.processes["R"].state,
            ProcessState.WAITING_EXTERNAL,
        )

        # Recreate every application object except the durable PostgreSQL data.
        store2 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        ledger2 = PostgresEventLedger(POSTGRES_DSN)
        telemetry2 = RecordingTelemetry()
        coordinator2 = RuntimeCoordinator(
            state_store=store2,
            event_ledger=ledger2,
            telemetry=telemetry2,
            clock=FakeClock(seconds=10),
        )
        before_event = coordinator2.reconcile_published_events()
        self.assertEqual(
            before_event.graph.processes["R"].state,
            ProcessState.WAITING_EXTERNAL,
        )

        resumed = coordinator2.publish_external_event(
            RuntimeEvent(
                event_id=event_id,
                wait_key=wait_key,
                observed_at="T10",
                payload_ref="experiment:result",
            )
        )
        self.assertEqual(
            resumed.graph.processes["R"].state,
            ProcessState.READY_TO_RESUME,
        )


@unittest.skipUnless(
    RUN_INTEGRATION and DBOS_DSN,
    "dedicated semantic-execution DBOS integration only",
)
class DBOSDurableRuntimeIntegrationTests(unittest.TestCase):
    queue_name = "semantic-execution-test"

    @classmethod
    def setUpClass(cls) -> None:
        from dbos import DBOS, DBOSConfig  # type: ignore[import-not-found]

        def bounded_dispatch(envelope):
            return {
                "result_ref": (
                    "result:"
                    + envelope["work_kind"]
                    + ":"
                    + str(envelope["payload"].get("value", "none"))
                )
            }

        cls.DBOS = DBOS
        cls.workflow_fn = staticmethod(DBOS.workflow()(bounded_dispatch))
        config: DBOSConfig = {
            "name": "workspace-semantic-execution-spike",
            "application_version": "0.1.0",
            "system_database_url": DBOS_DSN,
            "dbos_system_schema": "dbos_semantic_execution_test",
        }
        DBOS(config=config)
        DBOS.launch()
        DBOS.register_queue(cls.queue_name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.DBOS.destroy(destroy_registry=True)

    def adapter(self) -> DBOSDurableRuntime:
        return DBOSDurableRuntime(
            workflow_fn=self.workflow_fn,
            registered_queues=frozenset({self.queue_name}),
        )

    def wait_terminal(
        self,
        runtime: DBOSDurableRuntime,
        work_id: str,
        *,
        timeout: float = 15.0,
    ):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = runtime.get_status(work_id=work_id)
            if status is not None and status.state in {
                DurableWorkState.COMPLETED,
                DurableWorkState.FAILED,
                DurableWorkState.CANCELLED,
            }:
                return status
            time.sleep(0.05)
        self.fail(f"durable work did not reach terminal state: {work_id}")

    def test_same_work_id_is_idempotent_and_conflicting_input_fails_closed(self):
        runtime = self.adapter()
        work_id = f"dbos-{uuid.uuid4()}"
        request = DurableWorkRequest(
            work_id=work_id,
            work_kind="reasoning_quantum",
            payload={"value": "v1"},
            queue_name=self.queue_name,
        )

        first = runtime.submit(request)
        self.assertEqual(first.work_id, work_id)
        duplicate = runtime.submit(request)
        self.assertEqual(duplicate.work_id, work_id)

        final = self.wait_terminal(runtime, work_id)
        self.assertEqual(final.state, DurableWorkState.COMPLETED)
        self.assertEqual(
            final.result_ref,
            "result:reasoning_quantum:v1",
        )

        conflicting = DurableWorkRequest(
            work_id=work_id,
            work_kind="reasoning_quantum",
            payload={"value": "v2"},
            queue_name=self.queue_name,
        )
        with self.assertRaises(DurableWorkConflict):
            runtime.submit(conflicting)

    def test_unknown_queue_fails_before_dbos_submission(self):
        runtime = self.adapter()
        with self.assertRaises(ValueError):
            runtime.submit(
                DurableWorkRequest(
                    work_id=f"dbos-{uuid.uuid4()}",
                    work_kind="reasoning_quantum",
                    payload={"value": "v"},
                    queue_name="not-registered",
                )
            )

    def test_adapter_never_calls_dbos_recv_for_semantic_external_waits(self):
        path = (
            SRC
            / "workspace_semantic_execution"
            / "adapters"
            / "dbos_runtime.py"
        )
        tree = ast.parse(path.read_text(), filename=str(path))
        recv_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "recv"
        ]
        self.assertEqual(recv_calls, [])


if __name__ == "__main__":
    unittest.main()
