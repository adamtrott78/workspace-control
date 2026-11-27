"""E3-C1 resource observer acceptance tests."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
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
)
from workspace_semantic_execution.application import RuntimeCoordinator  # noqa: E402
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    ExecutorSession,
    ExecutorSessionState,
    OperatorAckMode,
    OperatorAction,
    OperatorActionState,
    OperatorActionType,
    OperatorHumanRequirement,
    OperatorPostLocalSuccess,
    ProcessState,
)
from workspace_semantic_execution.ports import StateSnapshot  # noqa: E402


OBSERVER_PATH = (
    ROOT
    / "benchmarks"
    / "workspace-semantic-execution"
    / "resource_observer_v1.py"
)
SPEC = importlib.util.spec_from_file_location("e3_resource_observer_v1", OBSERVER_PATH)
assert SPEC is not None and SPEC.loader is not None
observer_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = observer_module
SPEC.loader.exec_module(observer_module)

ResourceObserver = observer_module.ResourceObserver
canonical_json = observer_module.canonical_json
durable_accounting = observer_module.durable_accounting


def _operator_action(
    action_id: str,
    *,
    status: OperatorActionState,
    human_requirement: OperatorHumanRequirement,
) -> OperatorAction:
    return OperatorAction(
        action_id=action_id,
        generation=4,
        action_type=OperatorActionType.OPEN_RECOVERY,
        status=status,
        priority_rank=1,
        queue_sequence=1,
        created_at="2026-11-24T00:00:00Z",
        task_id="workspace-semantic-execution-migration-v1",
        reasoning_process_id=None,
        process_generation=None,
        worker_slot_id=None,
        session_generation=None,
        executor_id=None,
        payload_ref=None,
        payload_sha256=None,
        human_requirement=human_requirement,
        ack_mode=OperatorAckMode.NONE,
        post_local_success=OperatorPostLocalSuccess.COMPLETE_AND_REQUERY,
    )


class SequenceClock:
    def __init__(self, values):
        self.values = iter(values)

    def __call__(self):
        return next(self.values)


class ResourceObserverTests(unittest.TestCase):
    def test_observer_does_not_mutate_runtime_or_graph_version(self):
        def make_runtime():
            coordinator = RuntimeCoordinator(
                state_store=InMemoryStateStore(),
                event_ledger=InMemoryEventLedger(),
                telemetry=RecordingTelemetry(),
                clock=FakeClock(),
            )
            coordinator.initialize(
                DomainKernel.create_graph([DomainKernel.create_process("P")])
            )
            return coordinator

        control = make_runtime()
        observed = make_runtime()
        observer = ResourceObserver(root_pid=os.getpid())

        for coordinator, attach_observer in (
            (control, False),
            (observed, True),
        ):
            if attach_observer:
                observer.sample(
                    coordinator.snapshot(),
                    state_backend="in_memory",
                    expected_object_counts={
                        "processes": 1,
                        "executor_sessions": 0,
                        "operator_actions": 0,
                    },
                    phase="before-claim",
                )
            coordinator.claim(
                "P",
                worker_id="W",
                lease_id="L",
                expected_generation=0,
            )
            if attach_observer:
                observer.sample(
                    coordinator.snapshot(),
                    state_backend="in_memory",
                    phase="after-claim",
                )
            coordinator.start(
                "P",
                lease_id="L",
                expected_generation=0,
            )
            if attach_observer:
                observer.sample(
                    coordinator.snapshot(),
                    state_backend="in_memory",
                    phase="after-start",
                )
            coordinator.recover(
                "P",
                expected_generation=0,
                reason="e3-canary",
            )

        control_final = control.snapshot()
        observed_final = observed.snapshot()
        self.assertEqual(observed_final.version, control_final.version)
        self.assertEqual(
            dumps_work_graph(observed_final.graph),
            dumps_work_graph(control_final.graph),
        )
        self.assertEqual(
            observed_final.graph.processes["P"].state,
            ProcessState.READY_TO_RESUME,
        )
        self.assertEqual(observed_final.graph.processes["P"].generation, 1)
        last_sample = observer.report()["samples"][-1]
        self.assertEqual(
            last_sample["durable_state"]["reasoning_processes"][
                "by_generation"
            ],
            {"0": 1},
        )

    def test_durable_accounting_counts_state_generation_and_operator_work(self):
        process = DomainKernel.create_process("P")
        process.state = ProcessState.READY_TO_RESUME
        process.generation = 2
        graph = DomainKernel.create_graph([process])
        graph.executor_sessions["slot"] = ExecutorSession(
            slot_id="slot",
            executor_id="instant",
            session_generation=3,
            state=ExecutorSessionState.READY,
        )
        graph.operator_actions["ready"] = _operator_action(
            "ready",
            status=OperatorActionState.QUEUED,
            human_requirement=OperatorHumanRequirement.RECOVERY_INTERACTION,
        )
        graph.operator_actions["awaiting"] = _operator_action(
            "awaiting",
            status=OperatorActionState.AWAITING_DURABLE_ACK,
            human_requirement=OperatorHumanRequirement.PASTE_AND_SUBMIT,
        )

        result = durable_accounting(
            StateSnapshot(version=11, graph=graph),
            state_backend="postgresql",
            expected_object_counts={
                "processes": 1,
                "executor_sessions": 1,
                "operator_actions": 2,
            },
        )

        self.assertEqual(result["state_backend"], "postgresql")
        self.assertEqual(result["graph_version"], 11)
        self.assertEqual(
            result["reasoning_processes"]["by_state_generation"],
            {"READY_TO_RESUME@2": 1},
        )
        self.assertEqual(
            result["executor_sessions"]["by_state_generation"],
            {"READY@3": 1},
        )
        self.assertEqual(result["operator_actions"]["by_generation"], {"4": 2})
        self.assertEqual(result["operator_actions"]["ready_manual_cycles"], 1)
        self.assertEqual(
            result["operator_actions"]["awaiting_durable_ack_total"], 1
        )
        self.assertEqual(
            result["operator_actions"]["sent_unconfirmed_current_binding"], 1
        )
        self.assertTrue(result["objects"]["matches"])

    def test_unavailable_proc_metrics_are_explicit_not_fabricated(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc_root = Path(tmp)
            pid = 100
            base = proc_root / str(pid)
            (base / "fd").mkdir(parents=True)
            (base / "fd" / "1").write_text("", encoding="utf-8")
            (base / "task" / str(pid)).mkdir(parents=True)
            (base / "task" / str(pid) / "children").write_text(
                "", encoding="utf-8"
            )
            fields = ["R"] + ["0"] * 30
            fields[11] = "10"
            fields[12] = "5"
            fields[19] = "100"
            (base / "stat").write_text(
                f"{pid} (e3 fake process) " + " ".join(fields),
                encoding="utf-8",
            )
            (base / "status").write_text(
                "VmRSS:\t128 kB\n"
                "VmHWM:\t256 kB\n"
                "Threads:\t2\n",
                encoding="utf-8",
            )

            observer = ResourceObserver(
                root_pid=pid,
                proc_root=proc_root,
                clock_ticks_per_second=100,
                monotonic_clock=SequenceClock([0.0]),
                wall_clock=lambda: "2026-11-24T00:00:00+00:00",
            )
            sample = observer.sample()

        process = sample["process_tree"]
        self.assertEqual(process["rss_bytes"]["value"], 128 * 1024)
        self.assertEqual(process["peak_rss_bytes"]["value"], 256 * 1024)
        self.assertEqual(process["thread_count"]["value"], 2)
        self.assertEqual(process["file_descriptor_count"]["value"], 1)
        self.assertEqual(process["pss_bytes"]["status"], "UNAVAILABLE")
        self.assertIsNone(process["pss_bytes"]["value"])
        self.assertEqual(
            process["cpu_user_delta_seconds"]["status"], "UNAVAILABLE"
        )
        self.assertEqual(
            sample["durable_state"]["status"], "UNAVAILABLE"
        )

    def test_sampling_gap_phase_timing_and_canonical_json(self):
        observer = ResourceObserver(
            root_pid=os.getpid(),
            sampling_interval_seconds=1.0,
            monotonic_clock=SequenceClock([0.0, 0.25, 1.0, 3.0, 3.2]),
            wall_clock=SequenceClock(
                [
                    "2026-11-24T00:00:00+00:00",
                    "2026-11-24T00:00:01+00:00",
                    "2026-11-24T00:00:02+00:00",
                    "2026-11-24T00:00:03+00:00",
                    "2026-11-24T00:00:04+00:00",
                ]
            ),
        )
        observer.begin_phase("canary")
        observer.sample(phase="canary")
        observer.sample(phase="canary")
        observer.sample(phase="canary")
        phase = observer.end_phase("canary")
        report = observer.report()

        self.assertEqual(phase["duration_seconds"], 3.2)
        self.assertEqual(report["sampling"]["sample_count"], 3)
        self.assertEqual(report["sampling"]["gap_count"], 1)
        self.assertEqual(
            report["sampling"]["estimated_missing_sample_count"], 1
        )
        self.assertFalse(report["open_phases"])
        encoded = canonical_json(report)
        self.assertEqual(encoded, canonical_json(report))
        self.assertEqual(json.loads(encoded), report)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(
            report["observer"]["gpu_telemetry"],
            "FORBIDDEN_NOT_COLLECTED",
        )
        self.assertEqual(
            report["observer"]["padataset_access"],
            "FORBIDDEN_NOT_USED",
        )


if __name__ == "__main__":
    unittest.main()
