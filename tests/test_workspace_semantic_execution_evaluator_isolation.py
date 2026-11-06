"""Tests for hidden-ephemeral evaluator isolation primitives."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "benchmarks/workspace-semantic-execution/resumable_reasoning_ephemeral_fixture_v1.py"
HARNESS = ROOT / "benchmarks/workspace-semantic-execution/resumable_reasoning_pilot_v1.py"

spec = importlib.util.spec_from_file_location("ephemeral_fixture", GENERATOR)
ephemeral = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(ephemeral)

h_spec = importlib.util.spec_from_file_location("reasoning_harness", HARNESS)
harness = importlib.util.module_from_spec(h_spec)
assert h_spec.loader is not None
h_spec.loader.exec_module(harness)


class EphemeralEvaluatorIsolationTests(unittest.TestCase):
    SEED = "11" * 32
    NONCE = "22" * 32

    def test_worker_packet_excludes_oracle_and_secret_material(self):
        bundle = ephemeral.generate_bundle(seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
        packet = ephemeral.worker_packet_material(bundle)
        serialized = json.dumps(packet, sort_keys=True)
        self.assertNotIn("evaluator_oracle", packet)
        self.assertNotIn(self.SEED, serialized)
        self.assertNotIn(self.NONCE, serialized)
        self.assertNotIn("expected_hypothesis", serialized)
        self.assertIn("oracle_commitment_sha256", serialized)

    def test_same_secret_material_is_deterministic(self):
        left = ephemeral.generate_bundle(seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
        right = ephemeral.generate_bundle(seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
        self.assertEqual(left, right)

    def test_different_seed_changes_fixture_and_oracle_commitment(self):
        left = ephemeral.generate_bundle(seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
        right = ephemeral.generate_bundle(seed_hex="33" * 32, seal_nonce_hex=self.NONCE)
        self.assertNotEqual(
            left["public_fixture"]["fixture_id"],
            right["public_fixture"]["fixture_id"],
        )
        self.assertNotEqual(
            left["public_seal"]["oracle_commitment_sha256"],
            right["public_seal"]["oracle_commitment_sha256"],
        )

    def test_seal_verifies_and_detects_oracle_tampering(self):
        bundle = ephemeral.generate_bundle(seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
        self.assertTrue(
            ephemeral.verify_bundle(
                public_fixture=bundle["public_fixture"],
                evaluator_oracle=bundle["evaluator_oracle"],
                public_seal=bundle["public_seal"],
                seal_nonce_hex=self.NONCE,
            )
        )
        tampered = json.loads(json.dumps(bundle["evaluator_oracle"]))
        first = sorted(tampered["experiment_results"])[0]
        tampered["experiment_results"][first]["p95_latency_ms"] += 1
        self.assertFalse(
            ephemeral.verify_bundle(
                public_fixture=bundle["public_fixture"],
                evaluator_oracle=tampered,
                public_seal=bundle["public_seal"],
                seal_nonce_hex=self.NONCE,
            )
        )

    def test_generated_oracle_is_compatible_with_objective_evaluator(self):
        bundle = ephemeral.generate_bundle(seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
        fixture = bundle["public_fixture"]
        oracle = bundle["evaluator_oracle"]
        criteria = oracle["terminal_criteria"]
        experiments = [group[0] for group in criteria["required_experiment_groups"]]
        observed = {
            experiment_id: harness.content_hash(oracle["experiment_results"][experiment_id])
            for experiment_id in experiments
        }
        submission = {
            "final_hypothesis": criteria["expected_hypothesis"],
            "rejected_hypotheses": list(criteria["required_rejected_hypotheses"]),
            "observed_results": observed,
            "addressed_observations": ["O2"],
            "rationale": "Contract-valid generated fixture submission.",
        }
        result = harness.evaluate_research_iterate(fixture, oracle, submission)
        self.assertTrue(result["passed"], result)

    def test_short_secrets_fail_closed(self):
        with self.assertRaises(ephemeral.EphemeralFixtureError):
            ephemeral.generate_bundle(seed_hex="aa", seal_nonce_hex=self.NONCE)
        with self.assertRaises(ephemeral.EphemeralFixtureError):
            ephemeral.generate_bundle(seed_hex=self.SEED, seal_nonce_hex="bb")


if __name__ == "__main__":
    unittest.main()
