"""Regression tests for the resumable-reasoning pilot harness."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "benchmarks/workspace-semantic-execution/resumable_reasoning_pilot_v1.py"
PUBLIC_PATH = ROOT / "benchmarks/workspace-semantic-execution/resumable_reasoning_research_fixture_v1.json"
ORACLE_PATH = ROOT / "benchmarks/workspace-semantic-execution/resumable_reasoning_research_oracle_v1.json"


spec = importlib.util.spec_from_file_location("resumable_reasoning_pilot_v1", HARNESS_PATH)
harness = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(harness)

PUBLIC = json.loads(PUBLIC_PATH.read_text())
ORACLE = json.loads(ORACLE_PATH.read_text())

INSTANT = {
    "provider": "openai",
    "model": "instant",
    "surface": "chat",
    "tier": "INSTANT",
}
FRONTIER = {
    "provider": "openai",
    "model": "frontier",
    "surface": "chat",
    "tier": "FRONTIER",
}


def packet(step: str) -> dict:
    return {
        "objective": PUBLIC["objective"],
        "step": step,
        "fixture_id": PUBLIC["fixture_id"],
        "invariants": ["no authority expansion", "objective validation required"],
    }


class FixtureIsolationTests(unittest.TestCase):
    def test_public_fixture_does_not_embed_terminal_answer_or_results(self):
        serialized = json.dumps(PUBLIC, sort_keys=True)
        self.assertNotIn("expected_hypothesis", serialized)
        self.assertNotIn("p95_latency_ms", serialized)
        self.assertEqual(PUBLIC["visibility"], "worker_visible")
        self.assertEqual(ORACLE["visibility"], "evaluator_only_do_not_supply_to_reasoning_worker")


class ExternalWaitTests(unittest.TestCase):
    def test_wait_wake_cycle_uses_no_model_polling(self):
        run = harness.new_run(
            arm="C_instant_stateless_resume",
            fixture_id=PUBLIC["fixture_id"],
            process_id="R-wait",
        )
        run = harness.claim_run(run, worker_id="W1", expected_generation=0)
        run = harness.request_external(
            run,
            expected_generation=0,
            invocation_id="I1",
            executor=INSTANT,
            context_packet=packet("choose first experiment"),
            request_id="REQ1",
            kind="experiment",
            payload_ref="E_queue_4x",
        )
        self.assertEqual(run["status"], "WAITING_EXTERNAL")
        with self.assertRaises(harness.BenchmarkContractError):
            harness.claim_run(run, worker_id="W2", expected_generation=0)

        result = harness.oracle_result(PUBLIC, ORACLE, experiment_id="E_queue_4x")
        run = harness.publish_external_result(
            run,
            request_id="REQ1",
            result_ref="oracle:E_queue_4x",
            result_hash=result["result_hash"],
        )
        self.assertEqual(run["status"], "READY_TO_RESUME")
        self.assertEqual(run["metrics"]["model_poll_invocations"], 0)
        self.assertEqual(run["metrics"]["deterministic_compute_operations"], 1)


class GenerationFencingTests(unittest.TestCase):
    def test_stale_generation_is_rejected_after_recovery(self):
        run = harness.new_run(
            arm="C_instant_stateless_resume",
            fixture_id=PUBLIC["fixture_id"],
            process_id="R-recovery",
        )
        run = harness.claim_run(run, worker_id="W1", expected_generation=0)
        run = harness.recover_run(run, new_worker_id="W2", expected_generation=0)
        self.assertEqual(run["generation"], 1)
        run = harness.claim_run(run, worker_id="W2", expected_generation=1)

        with self.assertRaises(harness.BenchmarkContractError):
            harness.checkpoint_continue(
                run,
                expected_generation=0,
                invocation_id="stale",
                executor=INSTANT,
                context_packet=packet("stale write"),
            )

        run = harness.checkpoint_continue(
            run,
            expected_generation=1,
            invocation_id="fresh",
            executor=INSTANT,
            context_packet=packet("fresh write"),
        )
        self.assertEqual(run["status"], "READY_TO_RESUME")


class RoutingDisciplineTests(unittest.TestCase):
    def test_decomposition_and_escalation_are_distinct(self):
        run = harness.new_run(
            arm="D_instant_decompose_critic",
            fixture_id=PUBLIC["fixture_id"],
            process_id="R-decompose",
        )
        run = harness.claim_run(run, worker_id="W1", expected_generation=0)
        run = harness.decompose(
            run,
            expected_generation=0,
            invocation_id="I-decompose",
            executor=INSTANT,
            context_packet=packet("oversized but separable"),
            children=[
                {"process_id": "R-decompose.1", "objective": "facet one"},
                {"process_id": "R-decompose.2", "objective": "facet two"},
            ],
            depth=1,
            evidence_refs=["size:facets=2"],
        )
        self.assertEqual(run["status"], "DECOMPOSED")
        self.assertEqual(run["metrics"]["decomposition_count"], 1)
        self.assertEqual(run["escalations"], [])

        hard = harness.new_run(
            arm="E_hybrid_escalation",
            fixture_id=PUBLIC["fixture_id"],
            process_id="R-hard",
        )
        hard = harness.claim_run(hard, worker_id="W2", expected_generation=0)
        with self.assertRaises(harness.BenchmarkContractError):
            harness.escalate(
                hard,
                expected_generation=0,
                invocation_id="I-bad-escalation",
                executor=INSTANT,
                context_packet=packet("hard residual"),
                reason="",
                lower_tier_evidence_refs=[],
            )
        hard = harness.escalate(
            hard,
            expected_generation=0,
            invocation_id="I-good-escalation",
            executor=INSTANT,
            context_packet=packet("hard residual after decomposition"),
            reason="Residual causal discrimination remains unresolved after two bounded lower-tier attempts.",
            lower_tier_evidence_refs=["attempt:1", "attempt:2"],
        )
        self.assertEqual(hard["status"], "ESCALATION_REQUIRED")
        self.assertEqual(len(hard["escalations"]), 1)


class ResearchEvaluatorTests(unittest.TestCase):
    def test_objective_evaluator_accepts_valid_two_cycle_conclusion(self):
        queue_result = harness.oracle_result(PUBLIC, ORACLE, experiment_id="E_queue_4x")
        retry_result = harness.oracle_result(PUBLIC, ORACLE, experiment_id="E_force_retry_reset")
        submission = {
            "final_hypothesis": "H_retry_state",
            "rejected_hypotheses": ["H_queue"],
            "observed_results": {
                "E_queue_4x": queue_result["result_hash"],
                "E_force_retry_reset": retry_result["result_hash"],
            },
            "addressed_observations": ["O2"],
            "rationale": "Load relief changes latency, but queue expansion does not remove abnormal retries while request-boundary retry reset does.",
        }
        verdict = harness.evaluate_research_iterate(PUBLIC, ORACLE, submission)
        self.assertTrue(verdict["passed"])
        self.assertEqual(verdict["score"], 1.0)

    def test_evaluator_rejects_shortcut_and_fabricated_result(self):
        submission = {
            "final_hypothesis": "H_retry_state",
            "rejected_hypotheses": ["H_queue"],
            "observed_results": {
                "E_force_retry_reset": "0" * 64,
            },
            "addressed_observations": ["O2"],
            "rationale": "shortcut",
        }
        verdict = harness.evaluate_research_iterate(PUBLIC, ORACLE, submission)
        self.assertFalse(verdict["passed"])
        self.assertIn("insufficient_experiment_cycles", verdict["violations"])
        self.assertIn(
            "fabricated_or_mismatched_result:E_force_retry_reset",
            verdict["violations"],
        )

    def test_terminal_completion_requires_passing_validator(self):
        queue_result = harness.oracle_result(PUBLIC, ORACLE, experiment_id="E_queue_4x")
        retry_result = harness.oracle_result(PUBLIC, ORACLE, experiment_id="E_disable_pool_reuse")
        submission = {
            "final_hypothesis": "H_retry_state",
            "rejected_hypotheses": ["H_queue"],
            "observed_results": {
                "E_queue_4x": queue_result["result_hash"],
                "E_disable_pool_reuse": retry_result["result_hash"],
            },
            "addressed_observations": ["O2"],
            "rationale": "Queue capacity is non-causal while disabling pooled lifecycle reuse collapses retry amplification.",
        }
        verdict = harness.evaluate_research_iterate(PUBLIC, ORACLE, submission)
        self.assertTrue(verdict["passed"])

        run = harness.new_run(
            arm="A_frontier_long_horizon",
            fixture_id=PUBLIC["fixture_id"],
            process_id="R-terminal",
        )
        run = harness.record_validator_result(
            run,
            validator_id=verdict["validator_id"],
            passed=verdict["passed"],
            score=verdict["score"],
            evidence_ref="validator:research_iterate_objective_v1",
            details={"violations": verdict["violations"]},
        )
        run = harness.claim_run(run, worker_id="WF", expected_generation=0)
        run = harness.finish_run(
            run,
            expected_generation=0,
            invocation_id="I-terminal",
            executor=FRONTIER,
            context_packet=packet("terminal synthesis"),
            submission=submission,
            evidence_refs=["validator:research_iterate_objective_v1"],
        )
        self.assertEqual(run["status"], "COMPLETED")
        self.assertEqual(harness.hard_gate_violations(run), [])
        metrics = harness.metrics_snapshot(run)
        self.assertEqual(metrics["frontier_invocations"], 1)
        self.assertTrue(metrics["durable_state_correct"])


if __name__ == "__main__":
    unittest.main()
