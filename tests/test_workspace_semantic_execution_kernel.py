"""Contract tests for the semantic-execution orchestration kernel reference."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
KERNEL_PATH = ROOT / "benchmarks/workspace-semantic-execution/kernel_reference_v1.py"

spec = importlib.util.spec_from_file_location("kernel_reference_v1", KERNEL_PATH)
kernel = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(kernel)


def complete_process(
    graph: dict,
    process_id: str,
    *,
    worker_id: str,
    lease_id: str,
    action_id: str,
) -> dict:
    process = graph["processes"][process_id]
    generation = process["generation"]
    graph = kernel.claim(
        graph,
        process_id,
        worker_id=worker_id,
        lease_id=lease_id,
        expected_generation=generation,
    )
    graph = kernel.start(
        graph,
        process_id,
        lease_id=lease_id,
        expected_generation=generation,
    )
    graph = kernel.record_effect(
        graph,
        process_id,
        action_id=action_id,
        idempotency_key=f"idem:{action_id}",
        target_ref=f"target:{action_id}",
        effect_hash=f"hash:{action_id}",
        executor_id="deterministic-test",
        observed_at="T1",
        lease_id=lease_id,
        expected_generation=generation,
    )
    graph = kernel.propose_terminal(
        graph,
        process_id,
        lease_id=lease_id,
        expected_generation=generation,
    )
    graph = kernel.begin_validation(graph, process_id)
    graph = kernel.record_validation(
        graph,
        process_id,
        validator_id="validator:test",
        passed=True,
        evidence_ref=f"evidence:{action_id}",
        observed_at="T2",
    )
    return graph


class GenerationAndLeaseTests(unittest.TestCase):
    def test_stale_generation_cannot_mutate_after_recovery(self):
        graph = kernel.new_graph([kernel.new_process("R1")])
        graph = kernel.claim(
            graph,
            "R1",
            worker_id="W1",
            lease_id="L1",
            expected_generation=0,
        )
        graph = kernel.start(
            graph,
            "R1",
            lease_id="L1",
            expected_generation=0,
        )
        graph = kernel.recover(
            graph,
            "R1",
            expected_generation=0,
            reason="worker disappeared",
        )

        self.assertEqual(graph["processes"]["R1"]["generation"], 1)
        self.assertEqual(graph["processes"]["R1"]["state"], "READY_TO_RESUME")

        with self.assertRaises(kernel.KernelContractError):
            kernel.record_effect(
                graph,
                "R1",
                action_id="A1",
                idempotency_key="I1",
                target_ref="target:1",
                effect_hash="hash:1",
                executor_id="executor:1",
                observed_at="T1",
                lease_id="L1",
                expected_generation=0,
            )

    def test_at_most_one_current_lease(self):
        graph = kernel.new_graph([kernel.new_process("R1")])
        graph = kernel.claim(
            graph,
            "R1",
            worker_id="W1",
            lease_id="L1",
            expected_generation=0,
        )
        with self.assertRaises(kernel.KernelContractError):
            kernel.claim(
                graph,
                "R1",
                worker_id="W2",
                lease_id="L2",
                expected_generation=0,
            )


class DependencyAndDecompositionTests(unittest.TestCase):
    def test_dependency_cannot_be_claimed_before_upstream_completion(self):
        graph = kernel.new_graph(
            [
                kernel.new_process("A"),
                kernel.new_process("B", dependencies=["A"]),
            ]
        )
        with self.assertRaises(kernel.KernelContractError):
            kernel.claim(
                graph,
                "B",
                worker_id="WB",
                lease_id="LB",
                expected_generation=0,
            )

        graph = complete_process(
            graph,
            "A",
            worker_id="WA",
            lease_id="LA",
            action_id="AA",
        )
        graph = kernel.claim(
            graph,
            "B",
            worker_id="WB",
            lease_id="LB",
            expected_generation=0,
        )
        self.assertEqual(graph["processes"]["B"]["state"], "CLAIMED")

    def test_decomposed_parent_resumes_only_after_every_child_completes(self):
        graph = kernel.new_graph([kernel.new_process("P")])
        graph = kernel.claim(
            graph,
            "P",
            worker_id="WP",
            lease_id="LP",
            expected_generation=0,
        )
        graph = kernel.start(
            graph,
            "P",
            lease_id="LP",
            expected_generation=0,
        )
        graph = kernel.decompose(
            graph,
            "P",
            children=[
                {"process_id": "P.1"},
                {"process_id": "P.2"},
            ],
            lease_id="LP",
            expected_generation=0,
        )
        self.assertEqual(graph["processes"]["P"]["state"], "WAITING_DEPENDENCIES")
        self.assertIsNone(graph["processes"]["P"]["lease_id"])

        graph = complete_process(
            graph,
            "P.1",
            worker_id="W1",
            lease_id="L1",
            action_id="A1",
        )
        graph = kernel.refresh_dependency_waits(graph, event_id="child-1-complete")
        self.assertEqual(graph["processes"]["P"]["state"], "WAITING_DEPENDENCIES")

        graph = complete_process(
            graph,
            "P.2",
            worker_id="W2",
            lease_id="L2",
            action_id="A2",
        )
        graph = kernel.refresh_dependency_waits(graph, event_id="child-2-complete")
        self.assertEqual(graph["processes"]["P"]["state"], "READY_TO_RESUME")

    def test_failed_child_does_not_satisfy_parent(self):
        graph = kernel.new_graph([kernel.new_process("P")])
        graph = kernel.claim(
            graph,
            "P",
            worker_id="WP",
            lease_id="LP",
            expected_generation=0,
        )
        graph = kernel.start(
            graph,
            "P",
            lease_id="LP",
            expected_generation=0,
        )
        graph = kernel.decompose(
            graph,
            "P",
            children=[{"process_id": "P.1"}],
            lease_id="LP",
            expected_generation=0,
        )
        graph = kernel.fail(graph, "P.1", reason="objective failure")
        graph = kernel.refresh_dependency_waits(graph, event_id="child-failed")
        self.assertEqual(graph["processes"]["P"]["state"], "WAITING_DEPENDENCIES")

    def test_recovery_does_not_satisfy_child_dependencies(self):
        graph = kernel.new_graph([kernel.new_process("P-recover")])
        graph = kernel.claim(
            graph,
            "P-recover",
            worker_id="WP",
            lease_id="LP",
            expected_generation=0,
        )
        graph = kernel.start(
            graph,
            "P-recover",
            lease_id="LP",
            expected_generation=0,
        )
        graph = kernel.decompose(
            graph,
            "P-recover",
            children=[
                {"process_id": "P-recover.1"},
                {"process_id": "P-recover.2"},
            ],
            lease_id="LP",
            expected_generation=0,
        )
        graph = kernel.recover(
            graph,
            "P-recover",
            expected_generation=0,
            reason="scheduler restart",
        )
        parent = graph["processes"]["P-recover"]
        self.assertEqual(parent["generation"], 1)
        self.assertEqual(parent["state"], "WAITING_DEPENDENCIES")
        with self.assertRaises(kernel.KernelContractError):
            kernel.claim(
                graph,
                "P-recover",
                worker_id="WP2",
                lease_id="LP2",
                expected_generation=1,
            )


class WaitTests(unittest.TestCase):
    def test_external_wait_releases_worker_and_does_not_poll_model(self):
        graph = kernel.new_graph([kernel.new_process("R")])
        graph = kernel.claim(
            graph,
            "R",
            worker_id="W",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.start(
            graph,
            "R",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.record_reasoning_quantum(
            graph,
            "R",
            expected_generation=0,
            lease_id="L",
        )
        before = graph["processes"]["R"]["reasoning_quanta"]
        graph = kernel.wait_external(
            graph,
            "R",
            wait_key="ci:123",
            lease_id="L",
            expected_generation=0,
        )
        self.assertEqual(graph["processes"]["R"]["state"], "WAITING_EXTERNAL")
        self.assertIsNone(graph["processes"]["R"]["worker_id"])
        self.assertIsNone(graph["processes"]["R"]["lease_id"])

        with self.assertRaises(kernel.KernelContractError):
            kernel.record_reasoning_quantum(
                graph,
                "R",
                expected_generation=0,
                lease_id="L",
            )

        graph = kernel.wake_external(
            graph,
            "R",
            wait_key="ci:123",
            event_id="ci:123:completed",
        )
        self.assertEqual(graph["processes"]["R"]["state"], "READY_TO_RESUME")
        self.assertEqual(graph["processes"]["R"]["reasoning_quanta"], before)

    def test_recovery_does_not_satisfy_external_wait(self):
        graph = kernel.new_graph([kernel.new_process("R-recover-wait")])
        graph = kernel.claim(
            graph,
            "R-recover-wait",
            worker_id="W",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.start(
            graph,
            "R-recover-wait",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.wait_external(
            graph,
            "R-recover-wait",
            wait_key="experiment:E1",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.recover(
            graph,
            "R-recover-wait",
            expected_generation=0,
            reason="process restart while experiment still running",
        )
        process = graph["processes"]["R-recover-wait"]
        self.assertEqual(process["generation"], 1)
        self.assertEqual(process["state"], "WAITING_EXTERNAL")
        self.assertEqual(process["wait_key"], "experiment:E1")

        with self.assertRaises(kernel.KernelContractError):
            kernel.claim(
                graph,
                "R-recover-wait",
                worker_id="W2",
                lease_id="L2",
                expected_generation=1,
            )

        graph = kernel.wake_external(
            graph,
            "R-recover-wait",
            wait_key="experiment:E1",
            event_id="experiment:E1:complete",
        )
        self.assertEqual(
            graph["processes"]["R-recover-wait"]["state"],
            "READY_TO_RESUME",
        )

    def test_recovery_does_not_satisfy_external_wait(self):
        graph = kernel.new_graph([kernel.new_process("R-recover-wait")])
        graph = kernel.claim(
            graph,
            "R-recover-wait",
            worker_id="W",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.start(
            graph,
            "R-recover-wait",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.wait_external(
            graph,
            "R-recover-wait",
            wait_key="experiment:E1",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.recover(
            graph,
            "R-recover-wait",
            expected_generation=0,
            reason="process restart while experiment still running",
        )
        process = graph["processes"]["R-recover-wait"]
        self.assertEqual(process["generation"], 1)
        self.assertEqual(process["state"], "WAITING_EXTERNAL")
        self.assertEqual(process["wait_key"], "experiment:E1")
        with self.assertRaises(kernel.KernelContractError):
            kernel.claim(
                graph,
                "R-recover-wait",
                worker_id="W2",
                lease_id="L2",
                expected_generation=1,
            )
        graph = kernel.wake_external(
            graph,
            "R-recover-wait",
            wait_key="experiment:E1",
            event_id="experiment:E1:complete",
        )
        self.assertEqual(
            graph["processes"]["R-recover-wait"]["state"],
            "READY_TO_RESUME",
        )


class EffectAndValidationTests(unittest.TestCase):
    def _running_graph(self) -> dict:
        graph = kernel.new_graph([kernel.new_process("R")])
        graph = kernel.claim(
            graph,
            "R",
            worker_id="W",
            lease_id="L",
            expected_generation=0,
        )
        return kernel.start(
            graph,
            "R",
            lease_id="L",
            expected_generation=0,
        )

    def test_duplicate_identical_effect_is_idempotent(self):
        graph = self._running_graph()
        kwargs = dict(
            action_id="A",
            idempotency_key="I",
            target_ref="target:A",
            effect_hash="hash:A",
            executor_id="executor",
            observed_at="T1",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.record_effect(graph, "R", **kwargs)
        graph = kernel.record_effect(graph, "R", **kwargs)
        self.assertEqual(len(graph["processes"]["R"]["effect_receipts"]), 1)

    def test_conflicting_duplicate_effect_fails_closed(self):
        graph = self._running_graph()
        graph = kernel.record_effect(
            graph,
            "R",
            action_id="A",
            idempotency_key="I",
            target_ref="target:A",
            effect_hash="hash:A",
            executor_id="executor",
            observed_at="T1",
            lease_id="L",
            expected_generation=0,
        )
        with self.assertRaises(kernel.KernelContractError):
            kernel.record_effect(
                graph,
                "R",
                action_id="A",
                idempotency_key="I",
                target_ref="target:A",
                effect_hash="DIFFERENT",
                executor_id="executor",
                observed_at="T1",
                lease_id="L",
                expected_generation=0,
            )

    def test_tool_success_alone_cannot_complete_work(self):
        graph = self._running_graph()
        graph = kernel.record_effect(
            graph,
            "R",
            action_id="A",
            idempotency_key="I",
            target_ref="target:A",
            effect_hash="hash:A",
            executor_id="executor",
            observed_at="T1",
            lease_id="L",
            expected_generation=0,
        )
        self.assertEqual(graph["processes"]["R"]["state"], "RUNNING")
        self.assertNotEqual(graph["processes"]["R"]["state"], "COMPLETED")

    def test_completion_requires_effect_and_passing_validation(self):
        graph = self._running_graph()
        with self.assertRaises(kernel.KernelContractError):
            kernel.propose_terminal(
                graph,
                "R",
                lease_id="L",
                expected_generation=0,
            )

        graph = kernel.record_effect(
            graph,
            "R",
            action_id="A",
            idempotency_key="I",
            target_ref="target:A",
            effect_hash="hash:A",
            executor_id="executor",
            observed_at="T1",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.propose_terminal(
            graph,
            "R",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.begin_validation(graph, "R")
        graph = kernel.record_validation(
            graph,
            "R",
            validator_id="V",
            passed=True,
            evidence_ref="evidence:postcondition",
            observed_at="T2",
        )
        self.assertEqual(graph["processes"]["R"]["state"], "COMPLETED")

    def test_failed_validation_returns_to_repairable_state(self):
        graph = self._running_graph()
        graph = kernel.record_effect(
            graph,
            "R",
            action_id="A",
            idempotency_key="I",
            target_ref="target:A",
            effect_hash="hash:A",
            executor_id="executor",
            observed_at="T1",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.propose_terminal(
            graph,
            "R",
            lease_id="L",
            expected_generation=0,
        )
        graph = kernel.begin_validation(graph, "R")
        graph = kernel.record_validation(
            graph,
            "R",
            validator_id="V",
            passed=False,
            evidence_ref="evidence:failed-postcondition",
            observed_at="T2",
        )
        self.assertEqual(graph["processes"]["R"]["state"], "READY_TO_RESUME")
        self.assertTrue(graph["processes"]["R"]["repair_required"])


class CrashBoundaryTests(unittest.TestCase):
    def test_crash_after_effect_before_checkpoint_preserves_receipt_and_fences_old_worker(self):
        graph = kernel.new_graph([kernel.new_process("R")])
        graph = kernel.claim(
            graph,
            "R",
            worker_id="W0",
            lease_id="L0",
            expected_generation=0,
        )
        graph = kernel.start(
            graph,
            "R",
            lease_id="L0",
            expected_generation=0,
        )
        graph = kernel.record_effect(
            graph,
            "R",
            action_id="A",
            idempotency_key="I",
            target_ref="target:A",
            effect_hash="hash:A",
            executor_id="executor",
            observed_at="T1",
            lease_id="L0",
            expected_generation=0,
        )
        graph = kernel.recover(
            graph,
            "R",
            expected_generation=0,
            reason="crash after external effect",
        )

        self.assertIn("I", graph["processes"]["R"]["effect_receipts"])

        with self.assertRaises(kernel.KernelContractError):
            kernel.propose_terminal(
                graph,
                "R",
                lease_id="L0",
                expected_generation=0,
            )

        graph = kernel.claim(
            graph,
            "R",
            worker_id="W1",
            lease_id="L1",
            expected_generation=1,
        )
        graph = kernel.start(
            graph,
            "R",
            lease_id="L1",
            expected_generation=1,
        )
        graph = kernel.propose_terminal(
            graph,
            "R",
            lease_id="L1",
            expected_generation=1,
        )
        graph = kernel.begin_validation(graph, "R")
        graph = kernel.record_validation(
            graph,
            "R",
            validator_id="V",
            passed=True,
            evidence_ref="evidence:effect-observed",
            observed_at="T2",
        )
        self.assertEqual(graph["processes"]["R"]["state"], "COMPLETED")
        self.assertEqual(len(graph["processes"]["R"]["effect_receipts"]), 1)


class AuthorityBoundaryTests(unittest.TestCase):
    def _candidate(self) -> dict:
        return kernel.candidate_action(
            action_id="A1",
            process_id="R1",
            process_generation=0,
            target_ref="github:repo@sha",
            executor_type="GITHUB_READ_ONLY",
            idempotency_key="idem:A1",
            preconditions=["source_sha_matches"],
            expected_effect="read exact repository state",
            postcondition_validator="validator:exact_sha_read",
        )

    def test_candidate_action_is_non_authoritative(self):
        candidate = self._candidate()
        self.assertEqual(candidate["authorization_state"], "UNDECIDED")

    def test_non_allow_decisions_cannot_compile_action_spec(self):
        candidate = self._candidate()
        for outcome in ("DENY", "ABSTAIN", "UNKNOWN"):
            with self.subTest(outcome=outcome):
                with self.assertRaises(kernel.KernelContractError):
                    kernel.compile_action_spec(
                        candidate,
                        authority_decision={
                            "decision_id": f"D:{outcome}",
                            "outcome": outcome,
                            "action_id": "A1",
                            "process_id": "R1",
                            "process_generation": 0,
                            "target_ref": "github:repo@sha",
                            "authority_scope_ref": "policy:scope",
                        },
                    )

    def test_allow_must_bind_exact_action_and_target(self):
        candidate = self._candidate()
        with self.assertRaises(kernel.KernelContractError):
            kernel.compile_action_spec(
                candidate,
                authority_decision={
                    "decision_id": "D1",
                    "outcome": "ALLOW",
                    "action_id": "OTHER",
                    "process_id": "R1",
                    "process_generation": 0,
                    "target_ref": "github:repo@sha",
                    "authority_scope_ref": "policy:scope",
                },
            )

        with self.assertRaises(kernel.KernelContractError):
            kernel.compile_action_spec(
                candidate,
                authority_decision={
                    "decision_id": "D-stale",
                    "outcome": "ALLOW",
                    "action_id": "A1",
                    "process_id": "R1",
                    "process_generation": 1,
                    "target_ref": "github:repo@sha",
                    "authority_scope_ref": "policy:scope",
                },
            )

        spec = kernel.compile_action_spec(
            candidate,
            authority_decision={
                "decision_id": "D2",
                "outcome": "ALLOW",
                "action_id": "A1",
                "process_id": "R1",
                "process_generation": 0,
                "target_ref": "github:repo@sha",
                "authority_scope_ref": "policy:scope",
            },
        )
        self.assertEqual(spec["authority_decision_id"], "D2")
        self.assertEqual(spec["target_ref"], "github:repo@sha")


class FailClosedTests(unittest.TestCase):
    def test_unknown_event_fails_closed_without_mutation(self):
        graph = kernel.new_graph([kernel.new_process("R")])
        before = kernel.snapshot(graph)
        with self.assertRaises(kernel.KernelContractError):
            kernel.apply_event(graph, "R", "TOTALLY_UNKNOWN")
        self.assertEqual(graph, before)

    def test_unknown_state_fails_closed(self):
        graph = kernel.new_graph([kernel.new_process("R")])
        graph["processes"]["R"]["state"] = "MAGIC"
        with self.assertRaises(kernel.KernelContractError):
            kernel.validate_graph(graph)


if __name__ == "__main__":
    unittest.main()
